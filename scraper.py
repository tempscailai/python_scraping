import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

try:
    import cloudscraper
    USE_CLOUDSCRAPER = True
except ImportError:
    USE_CLOUDSCRAPER = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# -------------------------------
# CATEGORY & SITEMAP DISCOVERY
# -------------------------------

def detect_category_page(base_url):
    """Try to find product listing pages automatically."""
    possible_paths = [
        "/shop/", "/store/", "/products/", "/collections/all/",
        "/category/", "/product-category/", "/catalog/",
        "/all-products/", "/shop-all/", "/items/",
    ]
    
    print("Searching for product pages...", file=sys.stderr)

    for path in possible_paths:
        test_url = urljoin(base_url, path)
        try:
            r = requests.get(test_url, headers=HEADERS, timeout=10)
            if r.status_code == 200 and "product" in r.text.lower():
                print(f"Found product page: {test_url}", file=sys.stderr)
                return test_url
        except:
            pass

    print("No category discovered → using homepage", file=sys.stderr)
    return base_url


def get_product_links_from_sitemap(base_url, visited=None):
    """Try to get product links from sitemap.xml."""
    if visited is None:
        visited = set()
    
    product_links = set()
    sitemap_urls = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
        urljoin(base_url, "/product-sitemap.xml"),
    ]
    
    for sitemap_url in sitemap_urls:
        if sitemap_url in visited:
            continue
        visited.add(sitemap_url)

        print(f"Checking sitemap: {sitemap_url}", file=sys.stderr)
        
        try:
            resp = requests.get(sitemap_url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            root = ET.fromstring(resp.content)
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            urls = root.findall('.//ns:url/ns:loc', ns)
            for url in urls:
                url_text = url.text.lower()
                if any(x in url_text for x in ["/product/", "/products/", "/item/", "/p/"]):
                    product_links.add(url.text)

        except:
            continue

    return product_links


# -------------------------------
# PRODUCT LINK DISCOVERY
# -------------------------------

def get_product_links(category_url):
    product_links = set()

    try:
        resp = requests.get(category_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

    except Exception as e:
        print(f"Failed to load category page: {e}", file=sys.stderr)
        return product_links

    # Common patterns
    selectors = [
        "a[href*='/product/']",
        "a[href*='/products/']",
        "a[href*='/item/']",
        "a[href*='/p/']",
    ]

    from urllib.parse import urlparse
    base_domain = urlparse(category_url).netloc

    for sel in selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if not href:
                continue
            full = urljoin(category_url, href)
            if urlparse(full).netloc == base_domain:
                product_links.add(full)

    return product_links


# -------------------------------
# PRODUCT EXTRACTION
# -------------------------------

def extract_product_data(url, session=None):
    try:
        if session:
            resp = session.get(url, headers=HEADERS, timeout=15)
        else:
            resp = requests.get(url, headers=HEADERS, timeout=15)

        if resp.status_code in [403, 429] or "Just a moment" in resp.text:
            print("Cloudflare block detected", file=sys.stderr)
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        name = soup.select_one("h1")
        if name:
            name = name.get_text(strip=True)
        else:
            name = ""

        # Extract price
        import re
        price = ""
        for elem in soup.find_all(text=re.compile(r"[\$₹€£]\s?\d")):
            m = re.search(r"[\$₹€£]\s?\d[\d,\.]*", elem)
            if m:
                price = m.group()
                break

        # Extract image
        image = ""
        img = soup.select_one("img")
        if img:
            src = img.get("src") or img.get("data-src") or ""
            image = urljoin(url, src)

        # Extract description
        desc = ""
        d = soup.select_one("p")
        if d:
            desc = d.get_text(strip=True)

        return {
            "name": name,
            "price": price,
            "description": desc,
            "imageUrl": image,
            "url": url
        }

    except Exception as e:
        print(f"Error extracting product: {e}", file=sys.stderr)
        return None


# -------------------------------
# MAIN SCRAPER
# -------------------------------

def scrape_site(base_url):
    print("=== Scraper Started ===", file=sys.stderr)

    links = get_product_links_from_sitemap(base_url)

    if not links:
        category = detect_category_page(base_url)
        links = get_product_links(category)

    print(f"Discovered {len(links)} product links", file=sys.stderr)

    # Cloudsraper session if available
    session = cloudscraper.create_scraper() if USE_CLOUDSCRAPER else requests.Session()

    data = []
    skipped = 0

    for i, url in enumerate(links, 1):
        print(f"Processing {i}/{len(links)}: {url}", file=sys.stderr)
        item = extract_product_data(url, session)
        if item:
            data.append(item)
        else:
            skipped += 1
        time.sleep(0.8)

    print(f"Summary: {len(data)} products, {skipped} skipped", file=sys.stderr)

    # IMPORTANT FIX → RETURN JSON TO FLASK/n8n
    return data


# --------------------------------
# CLI MODE
# --------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape_site(sys.argv[1])
    else:
        print("No URL given")

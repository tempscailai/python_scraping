import os
from flask import Flask, request, jsonify
import scraper

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def run_scraper():
    # GET mode: /?url=...
    if request.method == "GET":
        url = request.args.get("url")
    else:
        # POST mode: JSON { "URL": "https://..." }
        data = request.get_json(silent=True) or {}
        url = data.get("URL")

    if not url:
        return jsonify({
            "error": "No URL provided. Use GET ?url=... or POST JSON { 'URL': '...' }"
        }), 400

    result = scraper.scrape_site(url)
    return jsonify({"status": "ok", "result": result})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

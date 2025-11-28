import os
from flask import Flask, request, jsonify
import scraper

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def run_scraper():
    print("Headers:", dict(request.headers))
    print("Raw:", request.data)
    print("JSON:", request.get_json(silent=True))

    if request.method == "GET":
        url = request.args.get("url")
    else:
        data = request.get_json(silent=True)

        # n8n array format
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            url = data[0].get("URL")
        # normal JSON object
        elif isinstance(data, dict):
            url = data.get("URL")
        else:
            url = None

    if not url:
        return jsonify({
            "error": "No URL provided",
            "received_headers": dict(request.headers),
            "received_raw": request.data.decode(errors='ignore'),
            "received_json": request.get_json(silent=True)
        }), 400

    result = scraper.scrape_site(url)
    return jsonify({"status": "ok", "result": result})

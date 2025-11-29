import os
from flask import Flask, request, jsonify
import scraper

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def run():
    # POST JSON body
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        url = data.get("url") or data.get("URL")

        if not url:
            return jsonify({"error": "Missing URL"}), 400

        result = scraper.scrape_site(url)
        return jsonify({"status": "ok", "result": result}), 200

    # GET query param
    url = request.args.get("url")
    if not url:
        return jsonify({
            "error": "Please pass ?url=https://sitename.com OR send POST JSON {\"url\": \"...\"}"
        }), 400

    result = scraper.scrape_site(url)
    return jsonify({"status": "ok", "result": result}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

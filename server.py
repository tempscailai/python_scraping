import os
from flask import Flask, request, jsonify
import scraper

app = Flask(__name__)

@app.route("/")
def run():
    url = request.args.get("url")
    if not url:
        return jsonify({
            "error": "Please pass ?url=https://sitename.com to scrape"
        }), 400

    result = scraper.scrape_site(url)
    return jsonify({"status": "ok", "result": result})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

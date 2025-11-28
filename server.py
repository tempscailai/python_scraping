import os
from flask import Flask
import scraper  # your scraper logic in a separate file

app = Flask(__name__)

@app.route("/")
def run_scraper():
    result = scraper.run()   # call your real scraper
    return {"status": "ok", "result": result}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

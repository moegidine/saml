import os
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        host = os.getenv("FLASK_HOST", "127.0.0.1")
        port = os.getenv("FLASK_PORT", "5000")
        form_data = {"referrer": f"http://{host}:{port}/home", **request.form}
        response = requests.post("http://127.0.0.1:20000/", data=form_data)
        return response.content, response.status_code, response.headers.items()
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=(os.getenv("FLASK_DEBUG") != "0"))

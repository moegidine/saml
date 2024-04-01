import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

idps = [
    ["IDP1", "http://localhost:11000/sso"],
    ["IDP2", "http://localhost:11001/sso"],
    ["IDP3", "http://localhost:11002/sso"],
]


@app.route("/redirect", methods=["POST"])
def redirect():
    idp = request.form.get("idp", None)
    if idp is not None and idp != "":
        idp = list(filter(lambda x: x[0] == idp, idps))
        if len(idp) == 1:
            idp = idp[0][1]
        else:
            return None, 400
        response = requests.post(idp, data=request.form)
        return response.content, response.status_code, response.headers.items()
    return None, 400


@app.route("/select", methods=["GET", "POST"])
def select():
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    return render_template(
        "index.html",
        idps=idps,
        data=request.form["metadata"] if "metadata" in request.form else "",
        action=f"http://{host}:{port}/redirect",
        referrer=request.form["referrer"] if "referrer" in request.form else "",
    )


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=(os.getenv("FLASK_DEBUG") != "0"))

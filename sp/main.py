import os
import requests
from flask import Flask, Response, request, make_response
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
import datetime
from decode import decode
from encode import encode
from json import dumps, loads
import xml.etree.ElementTree as ET


app = Flask(__name__)

private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=4096, backend=default_backend()
)

namespaces = {
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}


@app.route("/", methods=["POST"])
def login():
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = os.getenv("FLASK_PORT", "5000")
    token = request.form.get("token", None)
    if token is not None and token != "":
        payload = {}
        try:
            payload = loads(decode(request.form["token"], private_key))
        except Exception:
            pass
        if payload.get("url", None) is not None:
            response = requests.get(payload["url"])
            if response.status_code == 200:
                metadata = response.text
                _root = ET.fromstring(metadata)
                certificate = ""
                _url = ""
                for key_descriptor in _root.findall(
                    ".//md:IDPSSODescriptor/md:KeyDescriptor", namespaces
                ):
                    key_use = key_descriptor.get("use")
                    if key_use == "encryption":
                        x509_certificate = key_descriptor.find(
                            ".//ds:X509Certificate", namespaces
                        )
                        if x509_certificate is not None:
                            certificate = x509_certificate.text
                for _leaf in _root.findall(
                    ".//md:IDPSSODescriptor/md:SingleSignOnService", namespaces
                ):
                    location = _leaf.get("Location")
                    if location is not None and location != "":
                        _url = location
                        break
                if (
                    certificate != ""
                    and _url != ""
                    and certificate is not None
                    and _url is not None
                ):
                    certificate = x509.load_pem_x509_certificate(
                        certificate.encode(), default_backend()
                    )
                    metadata = requests.get(f"http://{host}:{port}/mee").text
                    form_data = {
                        "metadata": metadata,
                        "token": payload["token"],
                        "referrer": request.form["referrer"]
                        if "referrer" in request.form
                        else "",
                    }
                    response = requests.post(_url, data=form_data)
                    return (
                        response.content,
                        response.status_code,
                        response.headers.items(),
                    )
    metadata = requests.get(f"http://{host}:{port}/mee").text
    form_data = {
        "metadata": metadata,
        "referrer": request.form["referrer"]
        if "referrer" in request.form
        else "",
    }
    response = requests.post("http://127.0.0.1:10000/select", data=form_data)
    return response.content, response.status_code, response.headers.items()


@app.route("/sls", methods=["POST"])
def sls():
    return None, 200


@app.route("/acs", methods=["POST"])
def acs():
    encrypted = request.data
    try:
        payload = loads(decode(encrypted, private_key))
        response = requests.get(payload["referrer"])
        js = f"<script>window.location.href = '{payload['referrer']}';</script>"
        response = make_response(
            response.content, response.status_code, response.headers.items()
        )
        response.set_data(js)
        token = encode(
            dumps({"url": payload["url"], "token": payload["token"]}),
            private_key.public_key(),
        )
        response.set_cookie("AppToken", token, max_age=60 * 60 * 24)
        return response
    except Exception as e:
        return str(e), 500


@app.route("/mee", methods=["GET"])
def mee():
    certificate_builder = x509.CertificateBuilder()
    certificate_builder = certificate_builder.subject_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(
                    NameOID.STATE_OR_PROVINCE_NAME, "California"
                ),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME, "My Organization"
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, "mywebsite.com"),
            ]
        )
    )
    certificate_builder = certificate_builder.issuer_name(
        x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(
                    NameOID.STATE_OR_PROVINCE_NAME, "California"
                ),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME, "My Organization"
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, "mywebsite.com"),
            ]
        )
    )
    certificate_builder = certificate_builder.not_valid_before(
        datetime.datetime.today() - datetime.timedelta(days=1)
    )
    certificate_builder = certificate_builder.not_valid_after(
        datetime.datetime.today() + datetime.timedelta(days=365)
    )
    certificate_builder = certificate_builder.public_key(
        private_key.public_key()
    )
    certificate_builder = certificate_builder.serial_number(
        x509.random_serial_number()
    )
    certificate_builder = certificate_builder.add_extension(
        x509.SubjectAlternativeName([x509.DNSName("mywebsite.com")]),
        critical=False,
    )
    certificate = certificate_builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend(),
    )
    pem_certificate = certificate.public_bytes(serialization.Encoding.PEM)
    metadata = ""
    with open("metadata.template.xml", "r") as file:
        metadata = file.read()
    metadata = metadata.replace(
        "{{{CERTIFICATE_PEM}}}", pem_certificate.decode()
    )
    metadata = metadata.replace(
        "{{{FLASK_HOST}}}", os.getenv("FLASK_HOST", "127.0.0.1")
    )
    metadata = metadata.replace(
        "{{{FLASK_PORT}}}", os.getenv("FLASK_PORT", "5000")
    )
    return Response(metadata, mimetype="text/plain")


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=(os.getenv("FLASK_DEBUG") != "0"))

import os
from flask import (
    Flask,
    Response,
    render_template,
    request,
    make_response,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
import datetime
import xml.etree.ElementTree as ET
import requests
from json import dumps, loads
from encode import encode
from decode import decode

app = Flask(__name__)

private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=4096, backend=default_backend()
)

namespaces = {
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}


@app.route("/sls", methods=["POST"])
def sls():
    return None, 200


@app.route("/sso", methods=["GET", "POST"])
def sso():
    error = None
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    try:
        token = None
        certificate = None
        _url = None
        if "token" in request.form:
            token = request.form["token"]
            try:
                payload = loads(decode(token, private_key))
                if payload["uid"] != "admin007":
                    return render_template(
                        "index.html",
                        error=error,
                        action=f"http://{host}:{port}/sso",
                        data=request.form["metadata"]
                        if "metadata" in request.form
                        else "",
                        referrer=request.form["referrer"]
                        if "referrer" in request.form
                        else "",
                    )
            except Exception:
                token = None
        if "metadata" in request.form:
            metadata = request.form["metadata"]
            if metadata is not None and metadata != "":
                _root = ET.fromstring(metadata)
                for key_descriptor in _root.findall(
                    ".//md:SPSSODescriptor/md:KeyDescriptor", namespaces
                ):
                    key_use = key_descriptor.get("use")
                    if key_use == "encryption":
                        x509_certificate = key_descriptor.find(
                            ".//ds:X509Certificate", namespaces
                        )
                        if x509_certificate is not None:
                            certificate = x509_certificate.text
                for _leaf in _root.findall(
                    ".//md:SPSSODescriptor/md:AssertionConsumerService",
                    namespaces,
                ):
                    location = _leaf.get("Location")
                    if location is not None and location != "":
                        _url = location
                        break
            if certificate is not None and certificate != "":
                certificate = x509.load_pem_x509_certificate(
                    certificate.encode(), default_backend()
                )
            if (
                certificate is not None
                and certificate != ""
                and _url is not None
                and _url != ""
                and token is not None
                and token != ""
            ):
                response = requests.post(
                    _url,
                    data=encode(
                        dumps(
                            {
                                "referrer": request.form["referrer"]
                                if "referrer" in request.form
                                else "",
                                "url": f"http://{host}:{port}/mee",
                                "token": encode(
                                    dumps(
                                        {
                                            "uid": "admin007",
                                        }
                                    ),
                                    private_key.public_key(),
                                ),
                            }
                        ),
                        certificate.public_key(),
                    ),
                )
                return (
                    response.content,
                    response.status_code,
                    response.headers.items(),
                )
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin":
            if "metadata" not in request.form or request.form["metadata"] == "":
                response = make_response(render_template("home.html"))
                token = encode(
                    dumps(
                        {
                            "uid": "admin007",
                        }
                    ),
                    private_key.public_key(),
                )
                response.set_cookie("DomainToken", token, max_age=60 * 60 * 24)
                return response
            elif (
                _url is not None
                and certificate is not None
                and not isinstance(certificate, str)
            ):
                response = requests.post(
                    _url,
                    data=encode(
                        dumps(
                            {
                                "referrer": request.form["referrer"]
                                if "referrer" in request.form
                                else "",
                                "url": f"http://{host}:{port}/mee",
                                "token": encode(
                                    dumps(
                                        {
                                            "uid": "admin007",
                                        }
                                    ),
                                    private_key.public_key(),
                                ),
                            }
                        ),
                        certificate.public_key(),
                    ),
                )
                return (
                    response.content,
                    response.status_code,
                    response.headers.items(),
                )
        else:
            error = "Invalid credentials"
    except KeyError:
        error = None
    return render_template(
        "index.html",
        error=error,
        action=f"http://{host}:{port}/sso",
        data=request.form["metadata"] if "metadata" in request.form else "",
        referrer=request.form["referrer"] if "referrer" in request.form else "",
    )


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

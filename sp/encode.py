from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from math import ceil
from base64 import b64encode


def encode(cleartxt, public_key):
    cleartxt = cleartxt.encode("utf-8")
    ciphertxt = b""
    for i in range(ceil(len(cleartxt) / 430)):
        ciphertxt = ciphertxt + public_key.encrypt(
            cleartxt[i * 430 : i * 430 + 430],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    return b64encode(ciphertxt).decode("utf-8")

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from math import ceil
from base64 import b64decode


def decode(ciphertxt, private_key):
    ciphertxt = b64decode(ciphertxt)
    cleartxt = b""
    for i in range(ceil(len(ciphertxt) / 512)):
        cleartxt = cleartxt + private_key.decrypt(
            ciphertxt[i * 512 : i * 512 + 512],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    return cleartxt

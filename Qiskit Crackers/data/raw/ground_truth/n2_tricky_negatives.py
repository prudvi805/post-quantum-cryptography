import hashlib

from cryptography.hazmat.primitives.asymmetric import padding


def design_doc_hash(text):
    rsa = {"name": "a local dictionary, not the library"}
    return hashlib.sha256(text.encode()).hexdigest(), rsa


def pss_config():
    return padding.PSS(mgf=padding.MGF1(hashlib.sha256), salt_length=32)


def compare_label(s):
    # RSA and DSA appear here only in a comment.
    return s.upper() == "RSA-LIKE"

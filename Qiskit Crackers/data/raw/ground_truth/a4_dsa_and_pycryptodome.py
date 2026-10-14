from Crypto.PublicKey import DSA, RSA
from Crypto.Signature import DSS


def dsa_signing_key():
    return DSA.generate(2048)  # EXPECT: DSA


def load_rsa_key(pem_text):
    return RSA.import_key(pem_text)  # EXPECT: RSA


def dss_signer(key):
    return DSS.new(key, "fips-186-3")

import jwt

SHARED_SECRET = "change-me"


def issue_hmac_token(payload):
    return jwt.encode(payload, SHARED_SECRET, algorithm="HS256")


def issue_rsa_token(payload, private_pem):
    return jwt.encode(payload, private_pem, algorithm="RS256")  # EXPECT: RSA


def issue_ecdsa_token(payload, private_pem):
    return jwt.encode(payload, private_pem, algorithm="ES256")  # EXPECT: ECC

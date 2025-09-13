# videoapi/cognito.py
import boto3
import hmac
import hashlib
import base64
import os
from botocore.exceptions import ClientError

COGNITO_REGION = os.environ.get("COGNITO_REGION", "ap-southeast-2")
COGNITO_USERPOOL_ID = os.environ.get("COGNITO_USERPOOL_ID", "ap-southeast-2_KUuRLDBYK")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "1nc5drgnphkq8i4d2rusnfoa36")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "ttsd47doobrmjbrv7fbkoe4smvviop002996m1g6h47drlqq7cu")  # optional if used

client = boto3.client("cognito-idp", region_name=COGNITO_REGION)


def get_secret_hash(username: str) -> str:
    """Compute Cognito secret hash if client secret is set"""
    if not COGNITO_CLIENT_SECRET:
        return None
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def sign_up_user(username: str, password: str, email: str) -> dict:
    """Sign up a new user"""
    params = {
        "ClientId": COGNITO_CLIENT_ID,
        "Username": username,
        "Password": password,
        "UserAttributes": [{"Name": "email", "Value": email}],
    }
    secret_hash = get_secret_hash(username)
    if secret_hash:
        params["SecretHash"] = secret_hash

    try:
        response = client.sign_up(**params)
        return response
    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])


def confirm_user(username: str, code: str) -> dict:
    """Confirm a user with code from email"""
    params = {
        "ClientId": COGNITO_CLIENT_ID,
        "Username": username,
        "ConfirmationCode": code,
    }
    secret_hash = get_secret_hash(username)
    if secret_hash:
        params["SecretHash"] = secret_hash

    try:
        response = client.confirm_sign_up(**params)
        return response
    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])


def authenticate_user(username: str, password: str) -> dict:
    """Authenticate a user and return Cognito tokens"""
    params = {
        "AuthFlow": "USER_PASSWORD_AUTH",
        "AuthParameters": {
            "USERNAME": username,
            "PASSWORD": password,
        },
        "ClientId": COGNITO_CLIENT_ID,
    }
    secret_hash = get_secret_hash(username)
    if secret_hash:
        params["AuthParameters"]["SECRET_HASH"] = secret_hash

    try:
        response = client.initiate_auth(**params)
        return response["AuthenticationResult"]
    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])

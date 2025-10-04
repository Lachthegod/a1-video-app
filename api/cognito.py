import boto3
import hmac
import hashlib
import base64
import json
from botocore.exceptions import ClientError
from parameter_store import load_parameters


parameters = load_parameters()

COGNITO_REGION = parameters.get("awsregion", "ap-southeast-2")
COGNITO_CLIENT_ID = parameters.get("cognitoclientid")


client = boto3.client("cognito-idp", region_name=COGNITO_REGION)


def get_secret_hash(username: str) -> str:
    if not get_secret():
        return None
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        get_secret().encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


def sign_up_user(username: str, password: str, email: str) -> dict:
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

        if "ChallengeName" in response:
            return {
                "challenge": response["ChallengeName"],
                "session": response["Session"],
                "parameters": response.get("ChallengeParameters", {}),
            }

        return response["AuthenticationResult"]

    except ClientError as e:
        raise Exception(e.response["Error"]["Message"])


def respond_to_mfa_challenge(
    username: str, session: str, code: str, challenge: str
) -> dict:
    params = {
        "ClientId": COGNITO_CLIENT_ID,
        "ChallengeName": challenge,
        "Session": session,
        "ChallengeResponses": {"USERNAME": username},
    }

    if challenge == "CUSTOM_CHALLENGE":
        params["ChallengeResponses"]["ANSWER"] = code
    elif challenge == "SMS_MFA":
        params["ChallengeResponses"]["SMS_MFA_CODE"] = code
    elif challenge == "SOFTWARE_TOKEN_MFA":
        params["ChallengeResponses"]["SOFTWARE_TOKEN_MFA_CODE"] = code
    elif challenge == "EMAIL_OTP":
        params["ChallengeResponses"]["EMAIL_OTP_CODE"] = code

    secret_hash = get_secret_hash(username)
    if secret_hash:
        params["ChallengeResponses"]["SECRET_HASH"] = secret_hash

    response = client.respond_to_auth_challenge(**params)
    return response["AuthenticationResult"]


def get_secret(secret_name, region_name="ap-southeast-2"):

    client = boto3.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Error retrieving secret {secret_name}: {e}")

    secret_str = get_secret_value_response.get("SecretString")

    try:
        secret_dict = json.loads(secret_str)
        client_secret = secret_dict.get("client_secret")
        if not client_secret:
            raise RuntimeError(
                f"Secret {secret_name} does not contain 'client_secret' key"
            )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Secret {secret_name} is not valid JSON: {e}")

    return client_secret

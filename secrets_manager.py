import boto3
import json
from botocore.exceptions import ClientError


def get_secret(secret_name):
    client = boto3.client(service_name="secretsmanager", region_name="ap-southeast-2")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Error retrieving secret {secret_name}: {e}")

    secret_str = get_secret_value_response.get("SecretString")

    try:
        secret_dict = json.loads(secret_str)
        client_secret = secret_dict.get(secret_name)
        if not client_secret:
            raise RuntimeError(
                f"Secret {secret_name} does not contain '{secret_name}' key"
            )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Secret {secret_name} is not valid JSON: {e}")

    return client_secret

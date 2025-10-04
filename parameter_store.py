import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)


def load_parameters():
    names = [
        "/mirelle/COGNITO_USER_POOL_ID",
        "/mirelle/COGNITO_CLIENT_ID",
        "/mirelle/DOMAIN",
        "/mirelle/REDIRECT_URI",
        "/mirelle/S3_BUCKET_NAME",
        "/mirelle/DYNAMODB_TABLE",
    ]

    ssm = boto3.client("ssm", region_name="ap-southeast-2")
    params = {}

    for name in names:
        try:
            response = ssm.get_parameter(Name=name)
            key = name.replace("/mirelle/", "")
            params[key] = response["Parameter"]["Value"]
        except ClientError as e:
            logging.error(f"Failed to load parameter {name}: {e}")

    logging.info(f"Loaded parameters: {params}")
    return params

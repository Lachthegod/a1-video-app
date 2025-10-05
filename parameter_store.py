import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

# Cache for memoized parameters
_cached_parameters = None


def load_parameters():
    global _cached_parameters
    
    # Return cached parameters if already loaded
    if _cached_parameters is not None:
        return _cached_parameters
    
    params = {}
 
    names = [
        "/mirelle/COGNITO_USER_POOL_ID",
        "/mirelle/COGNITO_CLIENT_ID",
        "/mirelle/COGNITO_USER_POOL_DOMAIN",
        "/mirelle/DOMAIN",
        "/mirelle/REDIRECT_URI",
        "/mirelle/S3_BUCKET_NAME",
        "/mirelle/DYNAMODB_TABLE",
    ]

    ssm = boto3.client("ssm", region_name="ap-southeast-2")

    for name in names:
        try:
            response = ssm.get_parameter(Name=name)
            key = name.replace("/mirelle/", "")
            params[key] = response["Parameter"]["Value"]
        except ClientError as e:
            logging.error(f"Failed to load parameter {name}: {e}")

    logging.info(f"Loaded parameters: {params}")
    
    # Cache the parameters
    _cached_parameters = params
    return params

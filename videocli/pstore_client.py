import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

def load_parameters(names=None, region_name="ap-southeast-2"):
    if names is None:
        names = [
            "/n11715910/awsregion",
            "/n11715910/cognitouserpoolid",
            "/n11715910/cognitoclientid",
            "/n11715910/domain",
            "/n11715910/redirecturl",
            "/n11715910/s3bucket",
        ]

    ssm = boto3.client("ssm", region_name=region_name)
    params = {}

    for name in names:
        try:
            response = ssm.get_parameter(
                Name=name 
            )
            key = name.replace("/n11715910/", "")
            params[key] = response["Parameter"]["Value"]
        except ClientError as e:
            logging.error(f"Failed to load parameter {name}: {e}")

    return params
import boto3

def load_parameters(prefix="/n11715910", region_name="ap-southeast-2"):
    ssm = boto3.client("ssm", region_name=region_name)

    response = ssm.get_parameters_by_path(
        Path=prefix,
        Recursive=True,
        WithDecryption=False  
    )

    params = {}
    for param in response["Parameters"]:
        key = param["Name"].replace(prefix + "/", "")
        params[key] = param["Value"]

    return params
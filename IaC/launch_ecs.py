import boto3
import subprocess
import base64
import os

# ------------------------
# CONFIG
# ------------------------
REPO_NAME = "n11715910-a3-transcoder"
REGION = "ap-southeast-2"
DOCKER_IMAGE_NAME = "transcoder-worker:latest"
DOCKERFILE_PATH = "../videoworker"  # point to folder containing Dockerfile

# ------------------------
# ECR CLIENT
# ------------------------
ecr = boto3.client("ecr", region_name=REGION)

# ------------------------
# Create repository if not exists
# ------------------------
try:
    response = ecr.create_repository(repositoryName=REPO_NAME)
    repo_url = response["repository"]["repositoryUri"]
    print(f"Created repository: {repo_url}")
except ecr.exceptions.RepositoryAlreadyExistsException:
    response = ecr.describe_repositories(repositoryNames=[REPO_NAME])
    repo_url = response["repositories"][0]["repositoryUri"]
    print(f"⚠️ Repository already exists. Continuing with {repo_url}")

# ------------------------
# Build & push multi-arch Docker image directly to ECR
# ------------------------
tagged_image = f"{repo_url}:latest"
print(f"Building and pushing multi-arch Docker image {tagged_image}...")
subprocess.run(
    f"docker buildx create --use && "
    f"docker buildx build --platform linux/amd64,linux/arm64 "
    f"-t {tagged_image} --push {DOCKERFILE_PATH}",
    shell=True,
    check=True
)
print("✅ Multi-arch Docker image built and pushed successfully.")

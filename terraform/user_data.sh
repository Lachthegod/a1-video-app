#!/bin/bash
set -uo pipefail

# Install Docker
apt update
apt install awscli docker.io -y
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# Get image
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${api_ecr_repo_url}
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${client_ecr_repo_url}
docker pull ${api_ecr_repo_url}:latest
docker pull ${client_ecr_repo_url}:latest

run_container() {
  docker network rm -f app-network  || true
  docker network create app-network || true

  docker rm -f api
  docker rm -f client

  # Get AWS credentials from EC2 instance metadata
  TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)
  ROLE_NAME=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>/dev/null)
  CREDENTIALS=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME 2>/dev/null)
  
  AWS_ACCESS_KEY_ID=$(echo $CREDENTIALS | grep -o '"AccessKeyId" : "[^"]*' | cut -d'"' -f4)
  AWS_SECRET_ACCESS_KEY=$(echo $CREDENTIALS | grep -o '"SecretAccessKey" : "[^"]*' | cut -d'"' -f4)
  AWS_SESSION_TOKEN=$(echo $CREDENTIALS | grep -o '"Token" : "[^"]*' | cut -d'"' -f4)

  docker run -d \
    --name api \
    --restart always \
    --network app-network \
    -p 3000:3000 \
    -e AWS_REGION=${aws_region} \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    ${api_ecr_repo_url}:latest
  
  docker run -d \
    --name client \
    --restart always \
    --network app-network \
    -p 80:3001 \
    -e AWS_REGION=${aws_region} \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    ${client_ecr_repo_url}:latest
}

# Update image if needed
API_NEW_ID="$(docker image inspect -f '{{.Id}}' ${api_ecr_repo_url}:latest 2>/dev/null || echo '')"
API_OLD_ID="$(docker inspect -f '{{.Image}}' api 2>/dev/null || echo '')"
CLIENT_NEW_ID="$(docker image inspect -f '{{.Id}}' ${client_ecr_repo_url}:latest 2>/dev/null || echo '')"
CLIENT_OLD_ID="$(docker inspect -f '{{.Image}}' client 2>/dev/null || echo '')"

if [ "$API_NEW_ID" != "$API_OLD_ID" ] || [ -z "$API_OLD_ID" ] || [ "$CLIENT_NEW_ID" != "$CLIENT_OLD_ID" ] || [ -z "$CLIENT_OLD_ID" ]; then
  run_container
fi

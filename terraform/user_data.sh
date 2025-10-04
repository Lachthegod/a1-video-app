#!/bin/bash
set -uo pipefail

# Install Docker
apt update
apt install awscli docker.io -y
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# Get image
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repo_url}
docker pull ${ecr_repo_url}:latest

run_container() {
  docker rm -f app

  docker run -d \
    --name app \
    --restart always \
    -p ${port_host}:${port_container} \
    ${ecr_repo_url}:latest
}

# Update image if needed
NEW_ID="$(docker image inspect -f '{{.Id}}' ${ecr_repo_url}:latest 2>/dev/null || echo '')"
OLD_ID="$(docker inspect -f '{{.Image}}' app 2>/dev/null || echo '')"
if [ "$NEW_ID" != "$OLD_ID" ] || [ -z "$OLD_ID" ]; then
  run_container
fi

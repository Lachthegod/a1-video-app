aws ecr get-login-password --region ap-southeast-2 | \
docker login --username AWS --password-stdin 901444280953.dkr.ecr.ap-southeast-2.amazonaws.com

docker compose build
# docker compose push
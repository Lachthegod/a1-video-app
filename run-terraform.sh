aws sso login

terraform -chdir=terraform init
terraform -chdir=terraform apply -auto-approve

# Copy outputs to .env file
cat > .env <<EOF
API_ECR_REPO_URL=$(terraform -chdir=terraform output -raw api_ecr_repo_url)
CLIENT_ECR_REPO_URL=$(terraform -chdir=terraform output -raw client_ecr_repo_url)
EOF

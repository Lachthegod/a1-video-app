aws sso login

terraform -chdir=terraform init
terraform -chdir=terraform apply -auto-approve

# Copy outputs to .env file
cat > .env <<EOF
ECR_REPO_URL=$(terraform -chdir=terraform output -raw ecr_repo_url)
EOF

# Cognito
resource "aws_secretsmanager_secret" "cognito_client_secret" {
  name = "${var.project_prefix}/COGNITO_CLIENT_SECRET"
}
resource "aws_secretsmanager_secret_version" "cognito_client_secret" {
  secret_id     = aws_secretsmanager_secret.cognito_client_secret.id
  secret_string = aws_cognito_user_pool_client.client.client_secret
}
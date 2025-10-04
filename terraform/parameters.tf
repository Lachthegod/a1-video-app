# resource "aws_ssm_parameter" "api_url" {
#   name  = "/${var.project_prefix}/api/url"
#   type  = "String"
#   value = "https://${aws_apigatewayv2_api.app_api.api_endpoint}"
# }

# Route53
resource "aws_ssm_parameter" "domain" {
  name  = "/${var.project_prefix}/DOMAIN"
  type  = "String"
  value = var.domain
}

# S3
resource "aws_ssm_parameter" "s3_bucket_name" {
  name  = "/${var.project_prefix}/S3_BUCKET_NAME"
  type  = "String"
  value = aws_s3_bucket.app_bucket.bucket
}

# DynamoDB
resource "aws_ssm_parameter" "dynamodb_table" {
  name  = "/${var.project_prefix}/DYNAMODB_TABLE"
  type  = "String"
  value = "${var.project_prefix}-database"
}

# Cognito
resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name  = "/${var.project_prefix}/COGNITO_USER_POOL_ID"
  type  = "String"
  value = aws_cognito_user_pool.user_pool.id
}

resource "aws_ssm_parameter" "cognito_client_id" {
  name  = "/${var.project_prefix}/COGNITO_CLIENT_ID"
  type  = "String"
  value = aws_cognito_user_pool_client.client.id
}

resource "aws_ssm_parameter" "cognito_user_pool_domain" {
  name  = "/${var.project_prefix}/COGNITO_USER_POOL_DOMAIN"
  type  = "String"
  value = aws_cognito_user_pool_domain.domain.domain
}

# resource "aws_secretsmanager_secret" "api_keys" {
#   name        = "${var.project_prefix}-api-keys"
#   description = "External API keys for ${var.project_prefix}"
# }

# /*
# name        = "n11715910-a-s3-secret"
#   description = "S3 related secrets for n11715910-a"
# */

# resource "aws_secretsmanager_secret_version" "api_keys_value" {
#   secret_id     = aws_secretsmanager_secret.api_keys.id
#   secret_string = jsonencode({ s3_access = "REPLACE_ME" })
# }

# // secret_string = jsonencode({ external_api_key = "REPLACE_ME" })
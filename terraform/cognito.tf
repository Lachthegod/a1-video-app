resource "aws_cognito_user_pool" "user_pool" {
  name                     = "${var.project_prefix}-user-pool"
  auto_verified_attributes = ["email"]
  alias_attributes         = ["email", "preferred_username"]

  username_configuration {
    case_sensitive = false
  }

  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
  }

  email_configuration {
    email_sending_account = "DEVELOPER"
    from_email_address    = "\"Mirelle Mimiague\" <mirelle@cab432.com>"
    source_arn            = "arn:aws:ses:ap-southeast-2:901444280953:identity/cab432.com"
  }

  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = false
  }

  user_pool_add_ons {
    advanced_security_mode = "OFF"
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name                = "${var.project_prefix}-client"
  user_pool_id        = aws_cognito_user_pool.user_pool.id
  explicit_auth_flows = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  generate_secret     = true

  id_token_validity      = 1
  access_token_validity  = 1
  refresh_token_validity = 30

  # Federated login
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  supported_identity_providers = ["COGNITO", "Google"]
  callback_urls                = ["https://mirelle.cab432.com/auth/callback", "http://localhost:3001/auth/callback"]
}

resource "aws_cognito_user_pool_domain" "domain" {
  domain       = "mirelle"
  user_pool_id = aws_cognito_user_pool.user_pool.id
}

resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.user_pool.id
  provider_name = "Google"
  provider_type = "Google"

  attribute_mapping = {
    email              = "email"
    email_verified     = "email_verified"
    preferred_username = "name"
  }

  provider_details = {
    client_id        = var.google_client_id
    client_secret    = var.google_client_secret
    authorize_scopes = "openid email profile"
  }
}

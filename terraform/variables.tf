variable "aws_region" {
  default = "ap-southeast-2"
}

variable "aws_key_name" {
  default = "mirelle-key"
}

variable "project_prefix" {
  default = "mirelle"
}

variable "domain" {
  default = "mirelle.cab432.com"
}

variable "google_client_id" {
  default = "YOUR_GOOGLE_CLIENT_ID"
  sensitive = true
}

variable "google_client_secret" {
  default = "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"
  sensitive = true
}

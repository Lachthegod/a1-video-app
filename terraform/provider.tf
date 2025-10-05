terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.7.0"
    }
  }
}

provider "aws" {
  profile = "default"
  region  = var.aws_region
  default_tags {
    tags = {
      Environment   = "qut-username"
      qut-username  = "n10810315@qut.edu.au"
      purpose       = "assessment-3"
    }
  }
}

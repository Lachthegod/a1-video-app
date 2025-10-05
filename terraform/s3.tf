// S3 bucket (explicit name from the CloudFormation template)
resource "aws_s3_bucket" "app_bucket" {
  bucket        = "${var.project_prefix}-storage"
  force_destroy = true

  tags = {
    Project = "CAB432"
  }
}

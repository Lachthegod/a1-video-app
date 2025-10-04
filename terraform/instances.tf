resource "terraform_data" "cloudinit_fingerprint" {
  triggers_replace = filesha256("${path.module}/user_data.sh")
}

resource "aws_instance" "app" {
  ami                                  = data.aws_ami.ubuntu_22.id
  key_name                             = var.aws_key_name
  instance_type                        = "t3.micro"
  instance_initiated_shutdown_behavior = "terminate"
  security_groups                      = [data.aws_security_group.cab432_security_group.id]
  subnet_id                            = data.aws_subnet.public_subnet.id
  iam_instance_profile                 = "CAB432-Instance-Role"

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  user_data                   = data.cloudinit_config.userdata.rendered
  user_data_replace_on_change = true

  lifecycle {
    replace_triggered_by = [
      terraform_data.cloudinit_fingerprint
    ]

    ignore_changes = [ami, security_groups]
  }

  tags = {
    Name = "${var.project_prefix}-assessment"
  }
}

resource "aws_ecr_repository" "app" {
  name                 = "mirelle-assessment/app"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

data "cloudinit_config" "userdata" {
  gzip          = false
  base64_encode = false

  part {
    content_type = "text/cloud-config"
    content      = file("${path.module}/cloud-config-always.yml")
  }

  part {
    content_type = "text/x-shellscript"
    content = templatefile("${path.module}/user_data.sh", {
      aws_region     = var.aws_region
      ecr_repo_url   = aws_ecr_repository.app.repository_url
      port_host      = "3001"
      port_container = "3001"
    })
  }
}

output "ecr_repo_url" {
  value = aws_ecr_repository.app.repository_url
}
data "aws_security_group" "cab432_security_group" {
  name = "CAB432SG"
}

data "aws_subnet" "public_subnet" {
  filter {
    name   = "tag:Name"
    values = ["aws-controltower-PublicSubnet2"]
  }
}

data "aws_vpc" "main" {
  id = "vpc-007bab53289655834"
}

data "aws_ami" "ubuntu_22" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  owners = ["099720109477"]
}

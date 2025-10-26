import boto3
import base64

ec2 = boto3.client("ec2", region_name="ap-southeast-2")

# Template user_data with placeholders for dockerfile path and container name

user_data_script = """#!/bin/bash
# Update system packages
sudo apt-get update -y
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# Install Docker (official repo for latest version)
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Clone your repo
cd /home/ubuntu
git clone https://github.com/Lachthegod/a1-video-app.git
sudo chown -R ubuntu:ubuntu /home/ubuntu/a1-video-app
cd a1-video-app/{container_name}

# Run docker compose
sudo docker compose up -d --build
"""

# Define the microservices
microservices = [
    {"name": "apiservice"},
    # {"name": "webclient"},
    # {"name": "loginservice"},
    # {"name": "videoworker", "dockerfile": "videoworker/Dockerfile"},
]

# Launch each EC2 instance
for svc in microservices:
    user_data = user_data_script.format(
        container_name=svc["name"],
    )

    response = ec2.run_instances(
        LaunchTemplate={
            "LaunchTemplateId": "lt-0b457b274c9d5c21e",  
            "Version": "$Latest"
        },
        MinCount=1,
        MaxCount=1,
        UserData=base64.b64encode(user_data.encode("utf-8")).decode("utf-8"),
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [ 
                {"Key": "Name", "Value": svc["name"]},
                {"Key": "Project", "Value": "CAB432"}
            ]
        }]
    )

    instance_id = response["Instances"][0]["InstanceId"]
    print(f"Launched {svc['name']} on EC2 instance: {instance_id}")

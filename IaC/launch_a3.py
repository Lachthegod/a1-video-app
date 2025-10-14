import boto3
import base64

ec2 = boto3.client("ec2", region_name="ap-southeast-2")

# Template user_data with placeholders for dockerfile path and container name
USER_DATA_TEMPLATE = """#!/bin/bash
# Update system packages
sudo apt-get update -y
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# Install Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Clone repo
cd /home/ubuntu
git clone https://github.com/Lachthegod/a1-video-app.git
cd a1-video-app

# Build and run microservice
sudo docker build -f {dockerfile_path} -t {container_name} .
sudo docker run -d --name {container_name} -p {port}:{port} {container_name}
"""

# Define the microservices
microservices = [
    {"name": "apiservice", "dockerfile": "a1-video-app/apiservice/Dockerfile", "port": "3000"},
    # {"name": "webclient", "dockerfile": "a1-video-app/webclient/Dockerfile"},
    # {"name": "loginservice", "dockerfile": "a1-video-app/loginservice/Dockerfile"},
    # {"name": "videoworker", "dockerfile": "videoworker/Dockerfile"},
]

# Launch each EC2 instance
for svc in microservices:
    user_data = USER_DATA_TEMPLATE.format(
        dockerfile_path=svc["dockerfile"],
        container_name=svc["name"],
        port=svc["port"],
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

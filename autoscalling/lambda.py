import boto3
import os
import logging

# -----------------------------
# Logging setup
# -----------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -----------------------------
# Configuration
# -----------------------------
REGION = "ap-southeast-2"
QUEUE_URL = os.environ.get(
    "QUEUE_URL",
    "https://sqs.ap-southeast-2.amazonaws.com/901444280953/n11715910-a2"
)

# -----------------------------
# AWS clients
# -----------------------------
sqs = boto3.client("sqs", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

# -----------------------------
# Lambda handler
# -----------------------------
def lambda_handler(event, context):
    try:
        # 1. Get current queue size
        attrs = sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        queue_size = int(attrs['Attributes'].get('ApproximateNumberOfMessages', 0))
        logger.info(f"Queue size: {queue_size}")

        # 2. Publish SQS backlog as a custom CloudWatch metric
        cloudwatch.put_metric_data(
            Namespace='Custom/ECSAutoscaling',
            MetricData=[
                {
                    'MetricName': 'SQSQueueBacklog',
                    'Dimensions': [
                        {'Name': 'QueueName', 'Value': QUEUE_URL.split('/')[-1]}
                    ],
                    'Unit': 'Count',
                    'Value': queue_size
                }
            ]
        )
        logger.info(f"Published custom CloudWatch metric: {queue_size}")

    except Exception as e:
        logger.exception(f"Error in ECS autoscaling Lambda: {e}")

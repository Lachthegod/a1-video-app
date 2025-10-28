import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = "ap-southeast-2"
QUEUE_URL = os.environ.get(
    "QUEUE_URL",
    "https://sqs.ap-southeast-2.amazonaws.com/901444280953/n11715910-a2"
)

SCALE_FACTOR = 1
FIXED_INSTANCES = int(os.environ.get("FIXED_INSTANCES", 1))

sqs = boto3.client("sqs", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

def lambda_handler(event, context):
    try:
        # Get both visible and in-flight messages
        attrs = sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible'
            ]
        )
        visible_messages = int(attrs['Attributes'].get('ApproximateNumberOfMessages', 0))
        invisible_messages = int(attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        total_messages = visible_messages + invisible_messages
        logger.info(f"Total messages in queue (visible + in-flight): {total_messages}")

        in_service_instances = max(FIXED_INSTANCES, 1) 
        logger.info(f"Using fixed instance count: {in_service_instances}")

        messages_per_instance = (total_messages * SCALE_FACTOR) / in_service_instances
        logger.info(f"Messages per instance (weighted): {messages_per_instance}")

        cloudwatch.put_metric_data(
            Namespace='Custom/ECSAutoscaling',
            MetricData=[{
                'MetricName': 'MessagesPerInstance',
                'Dimensions': [{'Name': 'QueueName', 'Value': QUEUE_URL.split('/')[-1]}],
                'Unit': 'Count',
                'Value': messages_per_instance
            }]
        )
        logger.info("Published custom CloudWatch metric: MessagesPerInstance")

    except Exception as e:
        logger.exception(f"Error in ECS autoscaling Lambda: {e}")
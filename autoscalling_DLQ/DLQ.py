import boto3
import json
import logging
import os

# -----------------------------
# Configuration
# -----------------------------
MAIN_QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/901444280953/n11715910-a2"
REGION = "ap-southeast-2"
REQUIRED_FIELDS = ["video_id", "output_format", "filename", "input_key"]

# -----------------------------
# Logging
# -----------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# -----------------------------
# AWS Clients
# -----------------------------
sqs = boto3.client("sqs", region_name=REGION)

# -----------------------------
# Lambda Handler (triggered by SQS DLQ)
# -----------------------------
def lambda_handler(event, context):
    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])

            if all(field in body for field in REQUIRED_FIELDS):
                sqs.send_message(
                    QueueUrl=MAIN_QUEUE_URL,
                    MessageBody=json.dumps(body)
                )
                logger.info(f"Requeued valid message: {body['video_id']}")
            else:
                logger.warning(f"Deleting Invalid DLQ message (missing fields): {body}")

        except json.JSONDecodeError:
            logger.error(f"Deleting Malformed JSON in DLQ message: {record['body']}")
        except Exception as e:
            logger.exception(f"Unexpected error while processing message: {e}")


import base64
import json
import uuid
import logging
from typing import Any, Dict

import boto3
import os
import requests

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
textract = boto3.client('textract')

FILES_TABLE = os.environ['FILES_TABLE']
BUCKET_NAME = os.environ['BUCKET_NAME']


def create_file(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles the creation of a file. It decodes the base64-encoded file content from the request,
    generates a unique file ID, stores the file metadata in DynamoDB, uploads the file to S3,
    and updates the file status in DynamoDB.

    :param event: The event dictionary containing the request data.
    :param context: The context object provided by AWS Lambda.
    :return: A dictionary containing the HTTP status code and response body.
    """
    try:
        body = json.loads(event['body'])
        file_content = base64.b64decode(body['file'])

        # Generate a unique file ID
        file_id = str(uuid.uuid4())

        # Store file metadata in DynamoDB
        table = dynamodb.Table(FILES_TABLE)
        table.put_item(Item={
            'file_id': file_id,
            'status': 'UPLOADING'
        })
        logger.info("Stored file metadata in DynamoDB with file_id: %s", file_id)

        # Upload the file to S3
        s3_client.put_object(Bucket=BUCKET_NAME, Key=file_id, Body=file_content)
        logger.info("Uploaded file to S3 with file_id: %s", file_id)

        # Update the status in DynamoDB
        table.update_item(
            Key={'file_id': file_id},
            UpdateExpression="set #st = :s",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={':s': 'UPLOADED'}
        )
        logger.info("Updated file status in DynamoDB to 'UPLOADED' with file_id: %s", file_id)

        return {
            'statusCode': 200,
            'body': json.dumps({'file_id': file_id})
        }
    except Exception as e:
        # Log the error
        logger.error("Error processing file upload: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_file(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles the processing of a file. It retrieves the file from S3, extracts text using Amazon Textract,
    and updates the file status and extracted text in DynamoDB.

    :param event: The event dictionary containing the S3 event data.
    :param context: The context object provided by AWS Lambda.
    :return: A dictionary containing the HTTP status code and response body.
    """
    try:
        logger.info("Received event: %s", event)

        # Get the S3 bucket and object key from the event
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_key = event['Records'][0]['s3']['object']['key']

        # Retrieve the document from S3
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = s3_response['Body'].read()

        # Call Amazon Textract to detect text in the document
        textract_response = textract.detect_document_text(
            Document={'Bytes': file_content}
        )

        # Extract the detected text
        detected_text = " ".join([item['Text'] for item in textract_response['Blocks'] if item['BlockType'] == 'LINE'])

        # Update the item in DynamoDB
        table = dynamodb.Table(FILES_TABLE)
        table.update_item(
            Key={'file_id': object_key},
            UpdateExpression="SET #st = :s, #txt = :t",
            ExpressionAttributeNames={'#st': 'status', '#txt': 'text'},
            ExpressionAttributeValues={':s': 'PROCESSED', ':t': detected_text}
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'file_id': object_key, 'status': 'PROCESSED'})
        }
    except Exception as e:
        logger.error("Error processing file: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def make_callback(event: Dict[str, Any], context: Any) -> None:
    """
    Handles the callback to an external service when the file processing is completed.
    It sends the extracted text to the specified callback URL.

    :param event: The event dictionary containing the DynamoDB stream event data.
    :param context: The context object provided by AWS Lambda.
    """
    for record in event['Records']:
        if record['eventName'] == 'MODIFY':
            new_image = record['dynamodb']['NewImage']
            file_id = new_image['file_id']['S']
            status = new_image['status']['S']

            if status == 'COMPLETED':
                callback_url = new_image['callback_url']['S']
                text = new_image['text']['S']

                response = requests.post(callback_url, json={'file_id': file_id, 'text': text})
                logger.info("Sent callback to %s with response code %d", callback_url, response.status_code)


def get_file(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles the retrieval of file processing results. It fetches the file status and extracted text
    from DynamoDB and returns it to the client.

    :param event: The event dictionary containing the request data.
    :param context: The context object provided by AWS Lambda.
    :return: A dictionary containing the HTTP status code and response body.
    """
    file_id = event['pathParameters']['file_id']
    table = dynamodb.Table(FILES_TABLE)

    response = table.get_item(Key={'file_id': file_id})
    item = response.get('Item')

    if item:
        return {
            'statusCode': 200,
            'body': json.dumps({'file_id': file_id, 'status': item['status'], 'text': item.get('text')})
        }
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'File not found'})
        }

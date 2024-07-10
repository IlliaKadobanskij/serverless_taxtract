# Serverless Textract Project

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Deployment](#deployment)
- [Usage](#usage)

## Introduction
This project provides a serverless solution using AWS Lambda and Amazon Textract to extract text from uploaded files. It leverages API Gateway for HTTP endpoints and DynamoDB for file tracking.

## Prerequisites
- [Node.js and npm](https://nodejs.org/) installed
- [Serverless Framework](https://www.serverless.com/framework/docs/getting-started)
- AWS CLI configured with appropriate permissions

## Installation

### Download Serverless Framework
To install the Serverless Framework, run:
```
npm install -g serverless
```
### Install Plugins
Navigate to your project directory and run:
```
serverless plugin install -n serverless-plugin-common-excludes
serverless plugin install -n serverless-python-requirements
```

## Deployment

To deploy the project to AWS, run the following command:
```
serverless deploy --stage dev
```
This will deploy the services defined in `serverless.yml` to the AWS environment specified.

## Usage

### Example cURL Commands

#### Upload a File
```
curl -X POST https://{api_id}.execute-api.us-east-1.amazonaws.com/dev/files \
-H """Content-Type: application/json""" \
-d '{
    """file""": """BASE64_ENCODED_FILE_CONTENT""",
    """callback_url""": """https://your.callback.url/endpoint""" # optional
}'
```
For generating BASE64_ENCODED_FILE_CONTENT use ``generate_test_curl.py``

#### Get File Processing Status and Result
```
curl -X GET https://{api_id}.execute-api.us-east-1.amazonaws.com/dev/files/{file_id}
```
Replace `{api_id}` with your actual API Gateway ID and `{file_id}` with the unique identifier of your file.


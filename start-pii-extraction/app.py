import json
import urllib.parse
import boto3
import os

print('Loading function')

s3_client = boto3.client('s3')
comprehend_client = boto3.client('comprehend')

COMPREHEND_ROLE=os.environ['COMPREHEND_ROLE']
#'arn:aws:iam::257967673968:role/service-role/AmazonComprehendServiceRole-PII2'

def lambda_handler(event, context):
    print("Processing Event:")
    print(json.dumps(event))
    input_uri = event["S3INPUTURI"]
    output_uri = event["S3OUTPUTURI"]
    response = comprehend_client.start_pii_entities_detection_job(
        InputDataConfig={
            'S3Uri': input_uri, # 's3://piidataoutput/input/file.txt'
            'InputFormat': 'ONE_DOC_PER_FILE',
        },
        OutputDataConfig={
            'S3Uri': output_uri #'s3://piidataoutput/output/'
        },
        Mode='ONLY_OFFSETS',
        DataAccessRoleArn=COMPREHEND_ROLE,
        LanguageCode='en',
    )

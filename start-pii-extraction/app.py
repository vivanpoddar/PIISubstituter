import json
import urllib.parse
import boto3
import os
import datetime


print('Loading function')

s3_client = boto3.client('s3')
comprehend_client = boto3.client('comprehend')
s3_writer = boto3.resource('s3')


COMPREHEND_ROLE=os.environ['COMPREHEND_ROLE']
#'arn:aws:iam::257967673968:role/service-role/AmazonComprehendServiceRole-PII2'

def lambda_handler(event, context):
    now = datetime.datetime.now()
    print("Processing Event:")
    print(json.dumps(event))
    input_uri = event["S3INPUTURI"]
    output_uri = event["S3OUTPUTURI"] + str(now.strftime("%d.%m.%Y_%H.%M.%S"))

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
    stats = event
    stats["UI_TOPIC_ARN"] = event["UI_TOPIC_ARN"]
    o = urllib.parse.urlparse(output_uri, allow_fragments=False)
    account = boto3.client('sts').get_caller_identity().get('Account')
    statpath = os.path.join(o.path,account+"-PII-"+response["JobId"]+"/intermediate_stats.json").removeprefix('/')
    statsobj = s3_writer.Object(o.netloc, statpath)
    statsobj.put(Body=json.dumps(stats))
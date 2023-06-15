import boto3
import logging
import json
import urllib.parse
import os

logger = logging.getLogger(__name__)
client = boto3.client('comprehend')
from botocore.exceptions import ClientError
s3 = boto3.client("s3")

"""
response = client.start_pii_entities_detection_job(
    InputDataConfig={
        'S3Uri': 's3://piidataoutput/input/',
        'InputFormat': 'ONE_DOC_PER_FILE',
    },
    OutputDataConfig={
        'S3Uri': 's3://piidataoutput/output/'
    },
    Mode='ONLY_OFFSETS',
    DataAccessRoleArn='arn:aws:iam::257967673968:role/service-role/AmazonComprehendServiceRole-PII2',
    LanguageCode='en',
)
"""

def lambda_handler(event, context):
    print("Processing Event:")
    print(json.dumps(event))
    response = client.start_pii_entities_detection_job(
        InputDataConfig={
            'S3Uri': 's3://piidataoutput/input/',
            'InputFormat': 'ONE_DOC_PER_FILE',
        },
        OutputDataConfig={
            'S3Uri': 's3://piidataoutput/output/'
        },
        Mode='ONLY_OFFSETS',
        DataAccessRoleArn='arn:aws:iam::257967673968:role/service-role/AmazonComprehendServiceRole-PII2',
        LanguageCode='en',
    )

s3.download_file(
    Filename="data/input/input.txt",
    Bucket="piidataoutput",
    Key = "input/Untitled.txt"
)
s3.download_file(
    Filename="data/comprehend/comprehend_output.json",
    Bucket="piidataoutput",
    Key="output/257967673968-PII-03f87a2aa66e32c9d8e5f8f095dd1441/output/Untitled.txt.out"
)

comprehendOutput = open('data/comprehend/comprehend_output.json')
output = open('data/output/output.txt', 'a')
file = open('data/input/input.txt', 'r')
pii_entities = json.load(comprehendOutput)

iterators = {'address': 100, 'name': 0, 'bank_account_number': 1000, 'cvv': 1000, 'expiry': 2030, }
substitutions = {}
seekIndex = 0

output.write("")
for values in pii_entities["Entities"]: 
      
    start = int(values['BeginOffset'])
    end = int(values['EndOffset'])
    type = values['Type']
    text = ""

    for i in range(2):
        file.seek(seekIndex)
        if i==0 and pii_entities["Entities"].index(values)==0:
            output.write(file.read(start))
            seekIndex=start
        elif i % 2==0:
            output.write(file.read(start-seekIndex))
            seekIndex=start
        else:
            match type:
                case 'NAME':
                    text = 'John Doe'+str(iterators['name'])
                    iterators['name']+=1
                case 'ADDRESS':
                    text = str(iterators['address']) + ' Timbuktu Drive'
                    iterators['address']+=1
                case 'CREDIT_DEBIT_CVV':
                    text = iterators['cvv']
                    iterators['address']+=1
                case 'CREDIT_DEBIT_EXPIRY':
                    text = iterators['expiry']
                    iterators['expiry']+=1
                case 'BANK_ACCOUNT_NUMBER':
                    text = '5555-5555-5555-' + str(iterators['bank_account_number'])
                    iterators['bank_account_number']+=1
            output.write(text)
            substitutions[text] = file.read(end-start)              
            seekIndex=end

file.seek(end)
output.write(file.read())

print(substitutions)
output.close()
file.close()
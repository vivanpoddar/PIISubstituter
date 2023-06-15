import json
import urllib.parse
import boto3
import os

print('Loading function')

s3_writer = boto3.resource('s3')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')


def lambda_handler(event, context):
    print("Processing Event:")
    print(json.dumps(event))
    body = json.loads(event['Records'][0]["body"])['Records'][0]
    print(json.dumps(body))

    # Get the object from the event and show its content type
    bucket_name = body['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(body['s3']['object']['key'], encoding='utf-8')
    # "output/257967673968-PII-03f87a2aa66e32c9d8e5f8f095dd1441/output/Untitled.txt.out"
    input_file = 'input/' + os.path.splitext(os.path.basename(key))[0]

    stats_bucket = bucket_name
    stats_prefix = os.path.splitext(os.path.dirname(key))[0].removesuffix("/output")
    stat_key = os.path.join(stats_prefix, "intermediate_stats.json")
    print(stats_bucket, stat_key)
    stats = s3_client.get_object(Bucket=stats_bucket, Key=stat_key)['Body'].read().decode("utf-8")
    stats = json.loads(stats)

    s3_client.download_file(
        Filename='/tmp/input.txt',
        Bucket=bucket_name,
        Key = input_file
    )
    s3_client.download_file(
        Filename='/tmp/comprehend_output.json',
        Bucket=bucket_name,
        Key=key
    )

    comprehendOutput = open('/tmp/comprehend_output.json')
    output = open('/tmp/output.txt', 'a')
    file = open('/tmp/input.txt', 'r')
    pii_entities = json.load(comprehendOutput)

    iterators = {'address': 100, 'name': 0, 'bank_account_number': 1000, 'cvv': 1000, 'expiry': 2030, }
    substitutions = {}
    seekIndex = 0

    output.write("")
    for values in pii_entities["Entities"]: 
        
        start = int(values['BeginOffset'])
        end = int(values['EndOffset'])
        piitype = values['Type']
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
                if piitype == 'NAME':
                    text = 'John Doe'+str(iterators['name'])
                    iterators['name']+=1
                elif piitype == 'ADDRESS':
                    text = str(iterators['address']) + ' DocLens Steet; New York; NY 10024'
                    iterators['address']+=1
                elif piitype == 'CREDIT_DEBIT_CVV':
                    text = iterators['cvv']
                    iterators['address']+=1
                elif piitype == 'CREDIT_DEBIT_EXPIRY':
                    text = iterators['expiry']
                    iterators['expiry']+=1
                elif piitype == 'BANK_ACCOUNT_NUMBER':
                    text = '5555-5555-5555-' + str(iterators['bank_account_number'])
                    iterators['bank_account_number']+=1
                else:
                    print("unknown PII type:"+piitype)

                output.write(text)
                substitutions[text] = file.read(end-start)              
                seekIndex=end
                
    file.seek(end)
    output.write(file.read())

    #print(substitutions)
    output.close()
    file.close()

    try:
        pii_replaced_file = os.path.join('input-piisubst', os.path.basename(input_file))
        pii_substitutions_file = os.path.join('input-piisubst', os.path.basename(input_file) + ".subst.txt")
        print(pii_replaced_file)
        print(pii_substitutions_file)

        s3_client.upload_file('/tmp/output.txt', bucket_name, pii_replaced_file)
        print('Uploaded to bucket {} key {}'.format(bucket_name, pii_replaced_file))

        subst_object = s3_writer.Object(bucket_name, pii_substitutions_file)
        subst_object.put(Body=json.dumps(substitutions))

        ui_topic_arn = stats["UI_TOPIC_ARN"]
        sns_client.publish(
            TargetArn=ui_topic_arn,
            Message=json.dumps({
                "default": os.path.join(bucket_name,pii_replaced_file),
                'bucket': bucket_name,
                'pii_replaced_file': pii_replaced_file,
                'substitutions': pii_substitutions_file}),
            MessageStructure='json'
        )
        return 0
    except Exception as e:
        print(e)
        print('Error putting object {} into bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(pii_replaced_file, bucket_name))
        raise e
              
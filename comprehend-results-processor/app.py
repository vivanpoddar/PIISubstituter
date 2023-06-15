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

    body = json.loads(event["Records"][0]["body"])
    # Get the object from the event and show its content type
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    # "output/257967673968-PII-03f87a2aa66e32c9d8e5f8f095dd1441/output/Untitled.txt.out"
    input_file = 'input/' + os.path.splitext(os.path.basename(key))[0]

    stats_bucket = bucket_name
    stats_prefix = os.path.splitext(os.path.dirname(key))[0].removesuffix("/output")
    stat_key = os.path.join(stats_prefix, "intermediate_stats.json")
    print(stats_bucket, stat_key)
    stats = s3_client.get_object(Bucket=stats_bucket, Key=stat_key)['Body'].read().decode("utf-8")
    stats = json.loads(stats)

    pii_replaced_file = os.path.join(os.path.splitext(os.path.dirname(key))[0], os.path.splitext(os.path.basename(key))[0])
    pii_substitutions_file = os.path.join(os.path.splitext(os.path.dirname(key))[0], os.path.splitext(os.path.basename(key))[0] + ".subst.txt")

    s3_client.download_file(
        Filename="data/input/input.txt",
        Bucket=bucket_name,
        Key = input_file
    )
    s3_client.download_file(
        Filename="data/comprehend/comprehend_output.json",
        Bucket=bucket_name,
        Key=key
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

    try:
        response = s3_client.upload_file(output, bucket_name, pii_replaced_file)
        print("CONTENT TYPE: " + response['ContentType'])

        subst_object = s3_writer.Object(bucket_name, pii_substitutions_file)
        subst_object.put(Body=json.dumps(substitutions))

        ui_topic_arn = stats["UI_TOPIC_ARN"]
        sns_client.publish(
            TargetArn=ui_topic_arn,
            Message=json.dumps({
                "default": json.dumps(response),
                'bucket': bucket_name,
                'pii_replaced_file': pii_replaced_file,
                'substitutions': pii_substitutions_file}),
            MessageStructure='json'
        )
        return response['ContentType']
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
              
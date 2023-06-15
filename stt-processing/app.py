import boto3
import os
import datetime

TRANSCRIBE_ROLE=os.environ['TRANSCRIBE_ROLE']

def lambda_handler(event, context):

    # Retrieve the S3 bucket and object information from the event
    input_uri = event["S3INPUTURI"]
    output_uri = event["S3OUTPUTURI"]
    now = datetime.datetime.now()

    # Create an AWS Transcribe client
    transcribe_client = boto3.client('transcribe')
    
    # Set the input parameters for the transcription job
    job_name = "TranscriptionJob_" + str(now.strftime("%d.%m.%Y_%H.%M.%S")) # Specify a unique name for the job
    language_code = 'en-US'  # Replace with the actual language code
    
    # Start the transcription job
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': input_uri},
        LanguageCode=language_code,
        OutputBucketName=output_uri.split('/')[2],
        OutputKey = '/'.join(output_uri.split('/')[3:]),

        JobExecutionSettings={
            'AllowDeferredExecution': True,
            'DataAccessRoleArn': TRANSCRIBE_ROLE
        },
    )
    
    return {
        'statusCode': 200,
        'body': 'Transcription job started successfully'
    }







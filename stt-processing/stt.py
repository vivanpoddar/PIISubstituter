import boto3
client = boto3.client('transcribe')

def transcribe_file(job_name, file_uri, media_format):
    client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat=media_format,
        LanguageCode='en-US',
        OutputBucketName='lambdapiidatainput'
    )

def lambda_handler(event, context):
    transcribe_file('test2', 's3://lambdapiidatainput/input/test.wav', 'wav')







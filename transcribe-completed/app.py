import json

def lambda_handler(event, context):
    # Retrieve the Transcribe job details from the event
    job_name = event['detail']['TranscriptionJobName']
    job_status = event['detail']['TranscriptionJobStatus']
    
    # Process the Transcribe job details
    if job_status == 'COMPLETED':
        transcript_uri = event['detail']['Transcript']['TranscriptFileUri']
        # Perform further processing or actions with the completed Transcribe job
        
    # Log the Transcribe job details
    print(f"Transcription job {job_name} status: {job_status}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Transcribe job processing complete')
    }

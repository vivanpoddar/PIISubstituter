# A tool for redacting PII from legal documents for further processing by third-party services

Two Lambdas are currently functional, PIIExtractionFunction and ComprehendPIIResultsFunction

1. Deploy the sam template
2. For PIIExtractionFunction create an event with the following arguments: the SNS topic arn for the comprehend job, input s3 uri, output s3 uri
3. ComprehendPIIResultsFunction will be triggered through an SQS queue and your results will appear in the output s3 uri
The file ending in subst.txt contains a dictionary with the replaced PII entities and the word it was substituted with. 
The other file contains the original text input with the PII entity substitutions 

### Unfinished
- Transcribe text output PII extraction

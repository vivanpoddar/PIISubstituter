#!/usr/bin/env bash
set -x
set -e

S3_BUCKET=piibucketdoclens
INPUT_FILE=sam-template.yaml
OUTPUT_FILE=sam-template-output.yaml
SOURCE_BUCKET=lambdapiidatainput
DESTINATION_BUCKET=lambdapiidataoutput
STAGE_NAME=LATEST
VERSION=1-0-0
STACK_NAME=comprehend-lambda-$VERSION
PROFILE=default

sam validate --template-file $INPUT_FILE --profile $PROFILE

# Package the application
sam build --template-file $INPUT_FILE --profile $PROFILE

# Package the application
sam package --template-file $INPUT_FILE \
                           --output-template-file $OUTPUT_FILE \
                           --s3-bucket $S3_BUCKET \
                           --profile $PROFILE
# Deploy the application
sam deploy --template-file $OUTPUT_FILE \
                          --stack-name $STACK_NAME \
                          --parameter-overrides StageName=$STAGE_NAME S3BucketName=$S3_BUCKET SourceBucketName=$SOURCE_BUCKET DestinationBucketName=$DESTINATION_BUCKET \
                          --capabilities CAPABILITY_NAMED_IAM \
                          --profile $PROFILE

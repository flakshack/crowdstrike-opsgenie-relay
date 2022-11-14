import json
import boto3
import os
import sys
import urllib3  # Docs: https://urllib3.readthedocs.io/en/stable/user-guide.html

from base64 import b64decode

# Code to decrypt the OpsGenie API key, which is encrypted via AWS and stored as an environment variable
api_Key = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(os.environ['apiKey']),
    EncryptionContext={
        'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']
    })['Plaintext'].decode('utf-8')

# This handler is called when the API Gateway receives a GET/POST
def lambda_handler(event, context):
    return_status = 500
    return_body = 'An error occurred'

    try:
        
        # JSON data from CrowdStrike may be formatted with single-quotes instead
        # of double-quotes, which will cause a TypeError when we try to reference 
        # it as a dict.  Here we convert them just in case.
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']
        
        # To verify that this is actually from CrowdStrike, we'll check the
        # workflow_id that is passed in the meta section.  This code can be seen on
        # the URL bar when editing the Notification Workflow.  It will need to be updated
        # if we add additional workflows.
        workflows = [
            "12314515135113241231234124312346",
            "34122412341234123412341234124312"
        ]
        
        if body['meta']['workflow_id'] in workflows:
            # The message field is the SUBJECT for the OpsGenie page.  Here we set a friendly subject
            # based on the trigger_name that is passed by CrowdStrike in the meta fields.
            message = 'New CrowdStrike event has occurred'
            if 'new detection' in body['meta']['trigger_name'].lower():
                message = 'New CrowdStrike detection has occurred'
            elif 'new incident' in body['meta']['trigger_name'].lower:
                message = 'New CrowdStrike incident has occurred'
    
            # Loop through the events->body->data collection and add them to the description
            description= ''
            for key, value in body['data'].items():
    
                # Clean up the field names
                field_name = key.capitalize()
                if '.' in key:
                    # The key names use the format detections.XXXXXX, so strip out everything in front of the .
                    field_name = key.split('.')[1].capitalize() # Also capitalize the first letter
                    field_name = field_name.replace('_', ' ')   # Replace underscores with spaces
    
                new_line = field_name + ':  ' + value + '\n'    # Create the new line
                description += new_line                         # Add it to our description
            
            # OpsGenie API format: https://docs.opsgenie.com/docs/alert-api#create-alert
            post_data = {
                'message': message,
                'description': description
            }
            print(post_data)
            # Call the OpsGenie API to create the alert
            return_status, return_body = create_opsgenie_alert(post_data)
    
        else:
            # The workflow id didn't match, so just log it and don't create an alert.
            print("Unexpected workflow_id: " + body['meta']['workflow_id'] )

    except KeyError:
        print("The inbound fields were not as expected. Data received:")
        # Print out inbound parameters in CloudWatch log for debugging later
        print(event)
        print(sys.exc_info()[0])

    # The return value sent through the AWS API Gateway to CrowdStrike.
    return {
        'statusCode': return_status,
        'body': return_body
    }


# Call the OpsGenie API to create the alert
def create_opsgenie_alert(post_data):
    # Use urllib3 to create an alert in OpsGenie using their API.
    # docs here:  https://docs.opsgenie.com/docs/api-overview   
    http = urllib3.PoolManager()

    response = http.request(
        'POST',
        "https://api.opsgenie.com/v2/alerts", 
        body=json.dumps(post_data),
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'GenieKey ' + api_Key
        }
    )    

    # Pass the reply from OpsGenie so we can send back to CrowdStrike
    return response.status, response.data



    

    

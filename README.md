# crowdstrike-opsgenie-relay
We recently setup monitoring via CrowdStrike, but unfortunately they did not have any capability to send notifications directly to OpsGenie (although they support PagerDuty).  Since both companies have an API ability, I was able to write this AWS Lambda code to fix the CrowdStrike deficiency. This code can be used as a relay to reformat the CrowdStrike WebHook API to fit the OpsGenie API and create an alert.  

Lambda is a feature of AWS that allows you to run code on AWS without requiring a server.   You are charged per execution, which is great for systems (like this one), where it may be a long period between alerts from CrowdStrike. Once configured, you'll see nicely formatted CrowdStrike alerts in OpsGenie like this:

![image](https://user-images.githubusercontent.com/746386/136083922-67672e8c-8b4d-42a5-9dcb-e80892114108.png)

*Please note that although I'm happy to post this code and these directions, I don't generally have time to debug your personal configuration or otherwise assist you.  This setup works for me and hopefully gives you a head start on your own configuration.  There's an AWS Guide here:  AWS API Gateway Getting Started Guide	https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started.html*

## Step 1: Configure an API integration on OpsGenie and get an API Key

The first step here is to go into the OpsGenie settings and add an API integration.  Go to Settings, then click on "Integrations List" and click to add an "API integration."  Once configured, you'll see something similar to the below image.  The API key will be listed there, so make a copy of it to use later.

You may wish to check the box called "Suppress Notifications" while you work on this configuration to avoid actually paging anyone.  The alerts will still appear in the OpsGenie console.

![image](https://user-images.githubusercontent.com/746386/136084597-ad6f881b-b979-4d86-96d0-a7ae6a700530.png)

## Step 2:  Create the Lambda Function in AWS
*This assumes you already have an account in AWS.  Note that I'm not responsible for your AWS charges, so be sure that you understand how Lambda functions will be charged to your AWS account.*

Inside AWS, click on "Services" and select "Lambda."  Click on the "Create Function" button.  Supply a function name and select the runtime as Python 3.x. 

![image](https://user-images.githubusercontent.com/746386/136085454-222312ae-d44f-4025-b87c-acc0f7de1a50.png)

There are some other pages here that I didn't screenshot, but I just accepted the defaults.  Don't worry about adding the code yet, we'll get to that.

## Step 3:  Create the AWS API Gateway
Now that we have the Lambda function configured, we need to setup an API Gateway.  This will configure a URL on AWS that when called, will execute your Lambda function.  We'll give this URL to CrowdStrike and they'll do a POST action to this URL and pass through the JSON data for the alert.

Inside AWS, click on "Services" and select "API Gateway."  On the main page, click on the "Build" button to build an HTTP API.  Proceed through the "Create an API" wizard.  On the first step, select Lambda as the Integration type and select the name of your Lambda function as shown below.

![image](https://user-images.githubusercontent.com/746386/136086386-4bc3dc4d-319c-455c-80d3-d9e96e76b68e.png)

![image](https://user-images.githubusercontent.com/746386/136086515-2137f69a-34b4-408e-9282-cd1482054f81.png)

![image](https://user-images.githubusercontent.com/746386/136086557-9cd7f196-c74b-4c62-9c36-131ca6d76c6e.png)

![image](https://user-images.githubusercontent.com/746386/136086578-d5ac8c5d-eef3-45f7-a3dc-8b2ae176f71f.png)

Finally click "Create."

If you navigate back to the Lambda page, you'll now see your API gateway shown as a trigger for your Lambda function.  If you click on "Configuration...Triggers", you see the API endpoint listed.  This is the URL that we'll put inside CrowdStrike later.

![image](https://user-images.githubusercontent.com/746386/136088919-b6bf2efa-59a0-45e7-8727-e3ed223564e8.png)


## Step 4:  Create a KMS Key to encrypt your OpsGenie API key.
To be secure, we want to encrypt our OpsGenie API key.  This way it won't be visible in our code on AWS.

In AWS, click on Services and select Key Management Service.  Click on "Customer managed keys" and click "Create Key."  Here are some screenshots of the wizard.

![image](https://user-images.githubusercontent.com/746386/136087146-0ec96b29-87dc-4eed-af41-7ea4d4a15e17.png)
![image](https://user-images.githubusercontent.com/746386/136087180-6d6c5260-2bae-4995-bb0c-8356590855ff.png)

Add yourself as a key administrator (not shown, but check the box next to your name)

![image](https://user-images.githubusercontent.com/746386/136095948-8bf0a076-e7bf-4b3c-8da4-a99c8de2ad77.png)

Be sure to give the role that was created when you created the Lambda function access to this key.

![image](https://user-images.githubusercontent.com/746386/136087393-47cc4dac-0d30-4ca6-bc84-b074509bb7f1.png)

## Step 5:  Add the OpsGenie API Key as an encrypted environment variable

Navigate back to your Lambda function.  Click on "Configuration...Environment Variables."  Create a new Environment Variable called "apiKey."  The name has to match exactly, as it is referenced in our code.  

![image](https://user-images.githubusercontent.com/746386/136088079-8808ac84-4ca5-4068-a69d-cb85d559a3c2.png)

Click on the "Encryption in Transit" button and select the key that you created in Step 4 above.  You'll notice the sample code that we placed into our Lambda function, which allows us to decrypt the apiKey at runtime.

![image](https://user-images.githubusercontent.com/746386/136088125-a6f893a3-4de0-40d5-b381-7d4a8a055485.png)

## Step 6:  overwrite the lambda_function with the code from lambda_function.py

Copy the text of the code from this GitHub repository and paste it over the lambda_function.  Anytime you update the code, you'll need to click "Deploy."

![image](https://user-images.githubusercontent.com/746386/136089059-ca88e499-3b02-4bb2-9c10-ec4157ac1a10.png)

Click on "Test" and add paste in the JSON from test.json in this GitHub.  We can use this "Test Event" to pretend to be CrowdStrike sending an alert.


## Step 7:  Partial test of OpsGenie side

At this point, you should be able to perform a test that will create an alert in OpsGenie.  Note that the API url for OpsGenie is in the lambda_function, in the "create_opsgenie_alert" function.  If you are in the EU, you may have a different API endpoint.

Click on the Test button and review the Execution results.  If the results show a statusCode of 202, you should see a new alert appear in your OpsGenie queue.

![image](https://user-images.githubusercontent.com/746386/136090186-8094d9d9-eb5e-4067-bccc-9f0164819b86.png)

Note that there is a Workflow code in the sample data that matches the "workflows" in the main function.  We use this as an easy verification that the data is actually from the CrowdStrike Notification workflow.  Since you haven't created it yet, the workflow_id in the sample event matches the code.  You'll need to update this below before we go live.

## Step 8:  Create the Webhook entry in CrowdStrike

Once you've verified that that the OpsGenie side is working, you can configure the webhook on CrowdStrike.

Navigate to the CrowdStrike store and find the "Webhook" item.  Click Configure.  Give the Webhook a name and paste in the API Gateway URL from Step 3.  (Again, you can find it in AWS Lambda, in the Configuration...Triggers section.

![image](https://user-images.githubusercontent.com/746386/136091759-3e1405ee-a0ed-4fd2-bcc2-4485bc1caf8a.png)

## Step 9:  Create the Notification Workflow in CrowdStrike

In CrowdStrike, navigate to Configuration...Notification Workflows and create a new Workflow (if you don't already have one).  In the Edit Actions section, select "Call webhook" as the action and select the Webhook that you created in step 8.  In the Data to include section, specify the fields that you want to include in the alert.

![image](https://user-images.githubusercontent.com/746386/136092059-37f600f5-b3b1-4393-aabd-234a04208f81.png)


## Step 10:  Update the Workflow_ID codes

While on the Edit Notifications Workflow page in CrowdStrike, copy the Workflow ID from the URL bar.  This Workflow ID is passed along with each Webhook request to our Lambda function.  We use it as a simple verification method.

![image](https://user-images.githubusercontent.com/746386/136094742-46eb8f82-5678-4074-96d4-e65e850d100c.png)

Flip back to your AWS Lambda code and paste the Workflow ID into the code (I have 2 pretend codes listed there).  If you remove the existing codes, be sure to update your Test Event a Workflow ID that matches what is in the code.



## Step 10:  Test

Once everything is set, you can create a simple CrowdStrike test using this command (on a Windows computer that is running the CrowdStrike agent).
```
choice /m crowdstrike_sample_detection
```
It usually takes a few minutes for the alert to be processed by CrowdStrike.  On the Notifications Workflow page, you can click on the 3-dots and select "See Activity".  This will show you the alert from the CrowdStrike point of view.  If there is an error, you'll see something like this:

![image](https://user-images.githubusercontent.com/746386/136092747-16b8c279-7a8b-4841-be73-69eefc079c4a.png)

Once everything is working, be sure to remember to turn off "Suppress Notifications" for the configured API integration inside the OpsGenie settings.  Otherwise it won't ever actually do notifications, it will just appear in the Dashboard.


## Troubleshooting

On the Lambda page, you can click on the "Monitor" tab to review the logs for the lambda execution.  Click on the link in the LogStream to see the details.  Note that it can take several minutes for the logs to appear here.  Any output from the script (a print() function for example), will show here.

A good way to test is to include a print(event) in the main function so you can see what data came in from the API (i.e. what CrowdStrike is sending you.)

![image](https://user-images.githubusercontent.com/746386/136090988-3ca55b7e-392f-4a25-923e-630fe1a847f2.png)


## Disclaimer

I'm not an expert on anything, so you shouldn't trust any of this.  Your use of my code and/or these directions is at your own risk.  You are responsible for reviewing the code and these directions before you do anything on your systems (AWS, OpsGenie, CrowdStrike or others).  You are also responsible for any charges that AWS may make against you for your use of their features and services.





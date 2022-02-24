

Setting up the schemareg passthru api via python/fastapi app on the nodes is inherently problematic.   It requires installing several python packages, isn't resilient (really ought to be behind a load balancer).  A better solution would be to deploy this instead as a lambda function on AWS and make use of the AWS API Gateway to handle the request.


High level steps:
create a lambda function in your VPC
create an execution role
add a policy to the role

create api
create resource ==> method ==> resource {parameter}

add security policy to allow http traffic from the lambda

## Create Lambda Function


## Update IAM role/policy


## Update Security Group


## Create API

1. Go to the API Gateway console in AWS
2. BUILD a REST API that is only accessible from within a VPC
3. Create a new REST API, give it any name you like and make the Endpoint Type Private

### Add a Resource
4.  Click on the `/` and under the Actions menu pick `Create Resource`
5.  give it a name like `Schema Name`
  * Leave proxy resource unchecked
  * use `schema-name` for the resource path
  * Leave Enable API Gateway CORS unchecked
6.  Click `Create Resource`

### Add a Method
7.  Click on the resource you just created
8.  From the Actions dropdown, select `Create Method`
9.  A drop down will appear under your resource, select `GET`
10.  Press the checkmark button next to the method
11.  Select Lambda Function as the integration type
12.  Enable Lambda Proxy Integration
13.  Choose your region
14.  Type the name of your lambda function in the Lambda Function box
15.  Use the Default Timeout
16.  Click `Save`
17.  AWS will pop up an alert about some permissions it is about to assign, click `OK` (_it is always a good idea to understand what privs are minimally necessary_)


### Add a Resources for a path parameter
18.  Click on your method, and select `Create Resource` from the Actions dropdown.
19.  Do not configure as a proxy resource
20.  Name it `subject`
21.  Use `{subject}` for the Resource Path.   This will allow us to pass in the name of our schema registry object (which it calls a "subject") as a path parameter.


### Deploy your API
22.  Click on your method again, and select `Deploy API` from the Actions dropdown.
23.  Choose a deployment stage (or use an existing one).
  * Deployment stages are where your API will be deployed.   Think:  dev/test/prod
24.  Click `Deploy`

### See if it worked

Under Stages, click on your resource to see the URL for your API.  Note this has an AWS hostname followed by your deployment stage name, followed by your resource.  Paste that into a new browser window, and add your scheme registry object to the URL.

AWS Provided URL:  `https://3poig7ld4f.execute-api.us-east-2.amazonaws.com/test/schemaname`

add your schema registry subject name:

`https://3poig7ld4f.execute-api.us-east-2.amazonaws.com/test/schemaname/mySchemaRegistryEntry`

and you should see something like this return:

```
{"name": "MyClass", "type": "record", "namespace": "com.acme.avro", "fields": [{"name": "foo", "type": "string"}, {"name": "bar", "type": "string"}, {"name": "opt", "type": ["null", "string"], "default": null}]}
```








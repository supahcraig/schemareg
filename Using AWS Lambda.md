

Setting up the schemareg passthru api via python/fastapi app on the nodes is inherently problematic.   It requires installing several python packages, isn't resilient (really ought to be behind a load balancer).  A better solution would be to deploy this instead as a lambda function on AWS and make use of the AWS API Gateway to handle the request.


High level steps:
create a lambda function in your VPC
create an execution role
add a policy to the role

create api
create resource ==> method ==> resource {parameter}

add security policy to allow http traffic from the lambda

## Create Lambda Function

The code for the lambda function is in the `lambda_function.py` found in this repo.   The trick, is that we need to package it up with the requests library.

We need to clone this repo to get the lambda function code, then pip install requests into a new folder.   We will zip that up, and then add the lambda function to the zip.   This preserves the diretory structure that AWS Lambda requires.

```
git clone <this repo>
cd schemareg
mkdir package
pip install --target ./package requests
cd package
zip -r ../my-deployment.zip .
cd ..
zip -g my-deployment.zip lambda_function.py
```

### Actually Create the Lambda

1.  Go to the Lambda console in the AWS UI
2.  Click `Create Function`
3.  Author from scratch
4.  Give you function a name (any name you like)
5.  Runtime should be the latest Python version available (3.9 as of this writing)
6.  x86_64 architecture
7.  Under Permissions, create a new role with basic Lambda permissions (we'll update this later)
  * note the name of the IAM role it will create for you, you'll want it later  
8.  Under Advanced Settings
  * check Enable Network
  * Pick your VPC
  * Select the subnets you want your lambda deployed to
  * Select the security group you want to use (more on ths in a bit)
9.  Click `Create Function`


### Upload your Code

10.  Find the `Upload from` button above the code editor pane, and select `.zip file`
11.  Click `Upload` to navigate to your zip file
12.  Select your zip and click `Open`
13.  Click `Save`

You should see your Python code in the editor window, along with several folders related to the requests library we packed up eariler.

### Set up environment variables

The hostname of the schema registry will vary across CDP deployments.   The port will vary depending on if your CDP cluster is secured or not.   Regardless, these two values are baked into lambda environment variables which we much set up

14.  On the Code | Test | Monitor | Configureation | Aliases | Versions nav bar, click on `Configuration`
15.  Then click on `Environment Variables`, then click `Edit'
16.  Click `Add environment variable`
17.  Create 2 environement variables:
  * `key`: host `value`: your.private.ip.address
  * `key`: port `value`: 7788
18.  Click `Save`




## Update IAM role/policy

20.  Go to the IAM console in the AWS UI
21.  Search for the IAM role AWS created for you when you built your lambda
22.  Click `Add permissions` --> `Attach Policies`
23.  Filter for `AWSLambdaVPCAccesExecutionRole` which gives the necessary privs to work with ENIs & write logs. 


## Update Security Group

This step could vary depending on how you've got your cluster arranged with respect to security groups, so it may be best to just explain what traffic needs to be allowed & from where.

* The lambda function exists in a security group that you chose at create time
* The schema registry resides on an EC2 instance that has a security group attached
  * this security group needs to allow HTTP(?) traffic _from_ the security group that the lambda belongs to

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

*this is wrong*
should be a base resource, with the {resource} under it, and the GET method under the {resource}

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








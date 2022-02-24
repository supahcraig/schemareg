import json
import requests
import os

host = os.environ['host']
port = os.environ['port']

def lambda_handler(event, context):
    print(event) # to send this to CloudWatch
    schemaName = event['pathParameters']['subject'] # for resource path
    
    response = requests.get(f'http://{host}:{port}/api/v1/schemaregistry/schemas/{schemaName}/versions/latest').json()

    schematext = json.loads(response['schemaText'])

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(schematext)
    }

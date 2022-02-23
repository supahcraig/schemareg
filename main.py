from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import requests
import json

app = FastAPI()

# TODO: turn these into environment variables
schema_registry_host = 'cdp.3.128.74.236.nip.io'
schema_registry_port = 7788


@app.get('/schemaName/{subject}')
def schemaName(subject):

    schemareg_endpoint = 'http://{}:{}/api/v1/schemaregistry/schemas/{}/versions/latest'.format(
        schema_registry_host, schema_registry_port, subject)

    response = requests.get(schemareg_endpoint).json()

    schema_text = json.loads(response['schemaText'])
    print(schema_text)

    return JSONResponse(content=schema_text)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=18763)

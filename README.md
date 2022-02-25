# schemareg
To enable schema registry usage in Hive.  Whether or not this is something you _should_ do is left as an exercise for the reader.


The cloudera schema registry lacks an API to return a "clean" version of the schema, which Hive requires in order to read Avro data.   For what it's worth, the confluent schema registry has this functionality.  This allows Hive to gain the benefit of dynamic schema evolution, rather than maintaining a physical copy of the schema in HDFS and needing to point the hive table at that schema.   The hive table would also need to be rebuilt in the event of a schema change.   This solution gets around that limitation.

Through fastapi & uvicorn, we can use existing schema registry APIs to enable this functionality, which effectively enbales schema evolution in Hive.  Alternatively, the API could be served up as a lambda function via AWS API Gateway.  The former is much easier but has some drawbacks.   The latter has a more involved setup but overcomes nearly every shortcoming that our fastapi implementation creates.   




Other thoughts:

* probably run as a docker container or service
* add async?
* test running on multiple nodes behind the existing load balancer ==> this might be a trick
* developed against an unsecured cluster; needs to work on a kerberized cluster



# See it in action

Assumes you have an unsecured CDP cluster running nifi, schema registry, & hive.   This example uses HDFS, but it should work on s3 or ozone as well with minor tweaks.  More work needs to be done to make this work on a secured cluster.

## Schema Registry

Create a schema in the schema registry:

```
{
 "name": "MyClass",
 "type": "record",
 "namespace": "com.acme.avro",
 "fields": [
  {
   "name": "foo",
   "type": "string"
  },
  {
   "name": "bar",
   "type": "string"
  }
 ]
}
```


## Nifi setup overview

Most of this comes from the nifi setup portion of the Edge2AI demo


### Create the schema registry service

Under controller services, add a HortonworksSchemaRegistry
* `Schema Registry URL`:  <schema registry hostname>:7788/api/v1  I used the public hostname, but the private IP should work
* no SSL service, no kerberos



### GenerateFlowfile

`Mime Type`:  application/json

`Custom Text'`:
```
{"foo": "sample data", "bar": "more sample data"}
```


### UpdateAttribute 

Add a new property:
`schema.name`:  _your schema name_

### ConvertRecord
This converts the generatd JSON to Avro

#### JsonTreeReader

* `Schema Access Strategy`:  Use 'Schema Name' Property
* `Schema Registry`:  HortonworksSchemaRegistry (this is the schema registry service you created earlier)
* `Schema Name`:  ${schema.name}

#### AvroRecordSetWriter

* `Schema Write Strategy`:  Embed Avro Schema
* `Schema Access Strategy`:  Use 'Schema Name' Property
* `Schema Registry`:  HortonworksSchemaRegistry (this is the schema registry service you created earlier)
* `Schema Name`:  ${schema.name}


### PutHDFS

* `Hadoop Confuguration Resources`: find the path to core-site.xml & hdfs-site.xml
* `Directory`:  /user/nifi/incoming _or wherever you want to write your data to in HDFS_

This may require some HDFS permission work in order to write
 
 
## API setup

This can be done using fastapi, which requires a python program to run on one of your nodes, or you can use AWS Lambda + AWS API Gateway to host it instead.   Fastapi requires less steps, but Lambda is going to be more resilient.
 
### Lambda setup
https://github.com/supahcraig/schemareg/blob/master/Using%20AWS%20Lambda.md

 
### FastAPI setup
 
You'll need to have the fastapi API up and running before you create the table, or else it will fail.  SSH to a host...doesn't really matter which host, so long as the security groups & route tables allow traffic.

clone the repo

```
python3 main.py
```

Leave that window up, test the API by going to a web browswer and hit this URL:
  
`http://<host where your fastapi is running>:18763/schemaName/your_schema_name`
  
This should return a json object with your avro schema.   If it does, you're good to go.


## Hive Setup

```
create database test;
use test;
```

### Table DDL

_Change the location & schema name for your data_

```
CREATE EXTERNAL TABLE test.test_hive_ext
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.avro.AvroSerDe'
STORED as AVRO
LOCATION '/user/nifi/incoming/'
TBLPROPERTIES ('avro.schema.url'='http://cdp.3.128.74.236.nip.io:18763/schemaName/your_schema_name');
```

 *NOTE:* the URL for the avro schema will depend on your setup, and if you used fastapi or a lambda/api gateway.

Now test that it worked.   Selecting from the table should give you clean data back out.

`select * from test;`


## Test Schema Evolution

1.  Stop your nifi GenerateFlowfile processor
2.  Add a new field to the generated json:

```
{"foo": "sample data", "bar": "more sample data", "opt": "new optional field"}
```

3.  Go to the schema registry and update your schema with a new version that handles the new field with a default value

```
{
 "name": "MyClass",
 "type": "record",
 "namespace": "com.acme.avro",
 "fields": [
  {
   "name": "foo",
   "type": "string"
  },
  {
   "name": "bar",
   "type": "string"
  },
  {
   "name": "opt",
   "type": [
    "null",
    "string"
   ],
   "default": null
  }
 ]
}
```

4.  _before re-enabling your nifi generator_ test your Hive query again.  You should see a new field with the default value for the new field.
5.  Re-enable your GenerateFlowfile processor
6.  Run your Hive query one more time.  You should see actual data in the new field.
 
 
*NOTE:* initial testing showed this absolutely working as expected.   Subsequent tests don't show the new field populated with actual data; the default value is being pulled in.   Requires further investigation. 
 
## Troubleshooting
 
 * `[Error 90]` blah blah address alrady in use.   It's possible you have a prior instance of this thing running, find the pid and kill it.
 
 `ss -lnp | grep 18763`
 
 
 

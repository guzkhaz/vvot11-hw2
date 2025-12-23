import boto3
from config import app_config

session = boto3.Session(
    aws_access_key_id=app_config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app_config['AWS_SECRET_ACCESS_KEY'],
    region_name='ru-central1'
)

def get_ydb_client():
    endpoint = app_config['YDB_ENDPOINT']
    
    endpoint = f"https://{endpoint.replace('grpcs://', '')}" if endpoint and not endpoint.startswith('http') else endpoint

    return session.client('dynamodb',
                          endpoint_url=endpoint,
                          region_name='ru-central1')

def get_sqs_client():
    return session.client('sqs', endpoint_url=app_config['MQ_ENDPOINT'], region_name='ru-central1')
import os

app_config = {
    'WTF_CSRF_ENABLED': False,
    'YDB_ENDPOINT': os.environ.get('YDB_ENDPOINT'),
    'YDB_DATABASE': os.environ.get('YDB_DATABASE'),
    'MQ_ENDPOINT': os.environ.get('MQ_ENDPOINT'),
    'MQ_QUEUE_NAME': os.environ.get('MQ_QUEUE_NAME'),
    'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY'),
    'BUCKET_NAME': os.environ.get('BUCKET_NAME')
}
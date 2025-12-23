from clients import get_ydb_client

def create_table():
    ydb = get_ydb_client()

    try:
        ydb.describe_table(TableName='tasks')
    except ydb.exceptions.ResourceNotFoundException:
        try:
            ydb.create_table(
                TableName='tasks',
                KeySchema=[
                    {'AttributeName': 'task_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'task_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
            ydb.get_waiter('table_exists').wait(TableName='tasks')
        except Exception as e:
            print(f"Error creating table: {e}")
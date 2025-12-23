import os
import time
from file_utils import normalize_filename
from cloud_utils import get_boto_session


def upload_to_object_storage(file_path, task_id, task_title=""):
    try:
        session = get_boto_session()
        s3 = session.client('s3', endpoint_url='https://storage.yandexcloud.net')
        bucket = os.environ['BUCKET_NAME']

        ext = 'pdf' if file_path.endswith('.pdf') else 'txt'

        safe_title = normalize_filename(task_title)
        key = f"summaries/{task_id}_{safe_title}.{ext}"

        s3.upload_file(file_path, bucket, key)

        filename_for_download = f"{safe_title}.{ext}"

        return s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ResponseContentDisposition': f'attachment; filename="{filename_for_download}"'
            },
            ExpiresIn=604800
        )
    except Exception:
        return None


def update_task_status(task_id, status, error_message='', pdf_url=''):
    try:
        session = get_boto_session()
        ydb = session.client('dynamodb', endpoint_url=os.environ['YDB_ENDPOINT'])

        item = {
            'task_id': {'S': str(task_id)},
            'status': {'S': status},
            'updated_at': {'S': str(time.time())}
        }

        expr_vals = {':s': {'S': status}, ':e': {'S': error_message}}
        expr_names = {'#s': 'status', '#e': 'error_message'}
        update_expr = "SET #s = :s, #e = :e"

        if pdf_url:
            expr_vals[':u'] = {'S': pdf_url}
            expr_names['#u'] = 'pdf_url'
            update_expr += ", #u = :u"

        ydb.update_item(
            TableName='tasks',
            Key={'task_id': {'S': task_id}},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_vals,
            ExpressionAttributeNames=expr_names
        )
    except Exception:
        try:
            ydb.put_item(
                TableName='tasks',
                Item={
                    'task_id': {'S': task_id},
                    'status': {'S': status},
                    'error_message': {'S': error_message},
                    'task_title': {'S': 'Restored task'},
                    'video_url': {'S': '#'},
                    'created_at': {'S': str(time.time())}
                }
            )
        except Exception:
            pass
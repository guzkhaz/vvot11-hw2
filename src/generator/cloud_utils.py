import os
import boto3
import requests


def get_boto_session():
    return boto3.Session(
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name='ru-central1'
    )


def get_iam_token():
    try:
        url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
        headers = {"Metadata-Flavor": "Google"}
        response = requests.get(url, headers=headers, timeout=2)
        return response.json().get("access_token")
    except Exception:
        return None
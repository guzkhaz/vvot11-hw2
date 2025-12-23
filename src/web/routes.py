from flask import render_template, request, redirect, url_for, flash
import json
import uuid
from datetime import datetime
from clients import get_ydb_client, get_sqs_client
from database import create_table

def init_routes(app):
    @app.template_filter('format_datetime')
    def format_datetime(value):
        if not value:
            return "-"
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime('%d.%m.%Y %H:%M')
        except ValueError:
            return value

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/create/task', methods=['POST'])
    def create_task():

        ydb_client = get_ydb_client()
        
        task_title = request.form.get('task_title', '').strip()
        video_url = request.form.get('video_url', '').strip()
        task_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        try:
            ydb_client.put_item(
                TableName='tasks',
                Item={
                    'task_id': {'S': task_id},
                    'created_at': {'S': created_at},
                    'task_title': {'S': task_title},
                    'video_url': {'S': video_url},
                    'status': {'S': 'В очереди'},
                    'error_message': {'S': ''},
                    'pdf_url': {'S': ''}
                }
            )

            sqs_client = get_sqs_client()
            queue_url = sqs_client.get_queue_url(QueueName=app.config['MQ_QUEUE_NAME'])['QueueUrl']

            message = {
                'task_id': task_id,
                'task_title': task_title,
                'video_url': video_url
            }

            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message)
            )

            return redirect(url_for('tasks_list'))
        
        except Exception as e:
            flash(f"Error in task creation: {e}")
            return redirect(url_for('index'))

    @app.route('/tasks')
    def tasks_list():
        try:
            ydb_client = get_ydb_client()
            response = ydb_client.scan(TableName='tasks')
            tasks = response.get('Items', [])

            tasks.sort(
                key=lambda x: x.get('created_at', {'S': '1970-01-01T00:00:00'})['S'], 
                reverse=True
            )

            formatted_tasks = []
            for task in tasks:
                formatted_task = {
                    'task_id': task.get('task_id', {'S': 'unknown'})['S'],
                    'created_at': task.get('created_at', {'S': '-'})['S'],
                    'task_title': task.get('task_title', {'S': 'Без названия'})['S'],
                    'video_url': task.get('video_url', {'S': '#'})['S'],
                    'status': task.get('status', {'S': 'Неизвестно'})['S'],
                    'error_message': task.get('error_message', {'S': ''})['S'],
                    'pdf_url': task.get('pdf_url', {'S': ''})['S'],
                }
                formatted_tasks.append(formatted_task)

            return render_template('tasks.html', tasks=formatted_tasks)
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return render_template('tasks.html', tasks=[])
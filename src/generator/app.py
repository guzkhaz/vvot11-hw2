import os
import json
from flask import Flask, request, jsonify
from file_utils import normalize_filename
from cloud_utils import get_boto_session, get_iam_token
from media_processing import setup_ffmpeg, convert_to_mp3, download_video, validate_yandex_disk_url
from ai_services import audio_to_text, generate_summary
from document_generation import create_pdf
from storage_utils import upload_to_object_storage, update_task_status
from task_processor import process_message

app = Flask(__name__)


@app.route('/', methods=['POST'])
def handle_request():
    data = request.json
    messages = data.get('messages', [])
    for msg in messages:
        try:
            body = json.loads(msg['details']['message']['body'])
            process_message(body)
        except Exception as e:
            print(f"Message error: {e}")
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
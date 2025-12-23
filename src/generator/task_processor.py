import os
import tempfile
from cloud_utils import get_iam_token, get_boto_session
from media_processing import validate_yandex_disk_url, download_video, convert_to_mp3
from ai_services import audio_to_text, generate_summary
from document_generation import create_pdf
from storage_utils import upload_to_object_storage, update_task_status


def process_message(message_body):
    task_id = message_body.get('task_id')
    task_title = message_body.get('task_title', 'Unknown')
    video_url = message_body.get('video_url')
    iam_token = get_iam_token()

    if not iam_token:
        update_task_status(task_id, 'Ошибка', 'IAM Token Error')
        return

    bucket_name = os.environ['BUCKET_NAME']
    session = get_boto_session()
    s3_client = session.client('s3', endpoint_url='https://storage.yandexcloud.net')

    video_path = None
    mp3_path = None
    pdf_path = None
    temp_audio_key = f"temp_audio/{task_id}.mp3"

    try:
        if not validate_yandex_disk_url(video_url):
            raise Exception("Ссылка на видеофайл некорректная")

        update_task_status(task_id, 'В обработке', 'Скачивание видео')
        video_path = download_video(video_url, task_id)
        if not video_path: raise Exception("Download failed")

        update_task_status(task_id, 'В обработке', 'Конвертация')
        mp3_path = convert_to_mp3(video_path, task_id)
        if not mp3_path: raise Exception("Convert failed")

        s3_client.upload_file(mp3_path, bucket_name, temp_audio_key)

        update_task_status(task_id, 'В обработке', 'Распознавание речи')
        text = audio_to_text(bucket_name, temp_audio_key, iam_token)

        try:
            s3_client.delete_object(Bucket=bucket_name, Key=temp_audio_key)
        except:
            pass

        if not text: raise Exception("Распознавание речи не дало текста")

        update_task_status(task_id, 'В обработке', 'Генерация конспекта')
        summary = generate_summary(text, task_title, iam_token)
        final_text = summary if summary else text

        pdf_path = create_pdf(final_text, task_title, task_id)

        pdf_url = upload_to_object_storage(pdf_path, task_id, task_title)

        update_task_status(task_id, 'Успешно завершено', '', pdf_url)

    except Exception as e:
        update_task_status(task_id, 'Ошибка', str(e))
    finally:
        for p in [video_path, mp3_path, pdf_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
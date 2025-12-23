import os
import requests
import time


def audio_to_text(bucket_name, object_key, iam_token):
    file_uri = f"https://storage.yandexcloud.net/{bucket_name}/{object_key}"
    url_submit = "https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize"

    body = {
        "config": {
            "specification": {
                "languageCode": "ru-RU",
                "model": "general",
                "audioEncoding": "MP3",
                "literature_text": True
            }
        },
        "audio": {"uri": file_uri}
    }
    headers = {"Authorization": f"Bearer {iam_token}"}

    try:
        req = requests.post(url_submit, json=body, headers=headers)
        if req.status_code != 200:
            return None

        op_id = req.json()['id']

        for _ in range(120):
            time.sleep(5)
            res = requests.get(f"https://operation.api.cloud.yandex.net/operations/{op_id}", headers=headers).json()

            if res.get("done"):
                if "error" in res:
                    print(f"STT Operation Failed: {res.get('error')}")
                    return None

                response_data = res.get('response', {})
                chunks = response_data.get('chunks', [])

                text = " ".join([c['alternatives'][0]['text'] for c in chunks])
                return text

        return None

    except:
        return None


def generate_summary(text, task_title, iam_token):
    if not text:
        return None
    
    folder_id = os.environ['YC_FOLDER_ID']
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    text = text[:20000]

    prompt = (
        f"Создай подробный конспект лекции по теме '{task_title}'. "
        f"Разбей текст на логические блоки, выдели ключевые идеи, определения, примеры и выводы. "
        f"Текст лекции: {text}"
    )

    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "maxTokens": 2000,
            "temperature": 0.3
        },
        "messages": [{"role": "user", "text": prompt}]
    }
    headers = {"Authorization": f"Bearer {iam_token}", "x-folder-id": folder_id}

    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            return resp.json()['result']['alternatives'][0]['message']['text']
        return None
    except Exception:
        return None
import os
import shutil
import subprocess
import requests
import urllib
import tempfile
from urllib.parse import urlparse, unquote, urlencode


def setup_ffmpeg():
    src_path = os.path.join(os.getcwd(), 'ffmpeg')
    dst_path = '/tmp/ffmpeg'

    if not os.path.exists(src_path):
        return 'ffmpeg'

    if not os.path.exists(dst_path):
        shutil.copy2(src_path, dst_path)
        os.chmod(dst_path, 0o755)

    return dst_path


def convert_to_mp3(video_path, task_id):
    output_path = os.path.join(tempfile.gettempdir(), f"{task_id}.mp3")
    ffmpeg_bin = setup_ffmpeg()

    ffmpeg_cmd  = [
        ffmpeg_bin, '-y', '-i', video_path,
        '-vn', '-acodec', 'libmp3lame', '-b:a', '64k',
        output_path
    ]
    try:
        subprocess.run(
            ffmpeg_cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        
        return None
    except Exception as e:
        print(f"FFmpeg exception: {e}")
        return None


def validate_yandex_disk_url(url):
    if not url:
        return False

    if not any(domain in url for domain in ['disk.yandex.ru', 'disk.360.yandex.ru']):
        return False

    try:
        encoded_url = urllib.parse.quote(url, safe='')
        api_url = (
            f"https://cloud-api.yandex.net/v1/disk/public/resources"
            f"?public_key={encoded_url}"
        )
        
        response = requests.get(api_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('type') == 'file':
                return True
        return False
    except:
        return any(domain in url for domain in ['disk.yandex.ru', 'disk.360.yandex.ru'])

def download_video(url, task_id):
    try:
        public_key = url
        file_path = None

        parsed = urlparse(url)

        if '/d/' in parsed.path:
            path_parts = parsed.path.split('/')

            if len(path_parts) >= 3:
                key = path_parts[2]
                public_key = f"https://disk.yandex.ru/d/{key}"

                if len(path_parts) > 3:
                    file_path = '/' + '/'.join(
                        unquote(part) for part in path_parts[3:]
                    )

        base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download'
        params = {'public_key': public_key}

        if file_path:
            params['path'] = file_path

        final_url = f"{base_url}?{urlencode(params)}"
        response = requests.get(final_url)

        if response.status_code != 200:
            return None

        download_url = response.json().get('href')
        if not download_url:
            return None

        file_response = requests.get(download_url, stream=True)
        path = os.path.join(tempfile.gettempdir(), f"{task_id}.mp4")

        with open(path, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if os.path.getsize(path) < 1000:
            return None
        
        return path

    except Exception:
        return None
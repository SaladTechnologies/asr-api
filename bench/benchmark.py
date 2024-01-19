import threading
import queue
import requests
import os
import uuid
import subprocess
import shlex
import json
import time
import random
import re

audio_dir = os.getenv("AUDIO_DIR", "./audio")

download_dir = os.path.abspath(audio_dir)
os.makedirs(download_dir, exist_ok=True)

api_url = "http://localhost:8000/asr"

reporting_url = os.getenv("REPORTING_API_URL", "")
reporting_auth_header = os.getenv("REPORTING_AUTH_HEADER", "")
reporting_auth_value = os.getenv("REPORTING_API_KEY", "")
benchmark_id = os.getenv("BENCHMARK_ID", "")

reporting_headers = {
    reporting_auth_header: reporting_auth_value,
}


def wget_download(url, save_path):
    """
    Download a file from a URL using wget and save it to the specified path.

    :param url: URL of the file to download
    :param save_path: Path where the file should be saved
    """
    command = f"wget -q -O {shlex.quote(save_path)} {shlex.quote(url)}"
    try:
        subprocess.run(command, shell=True, check=True, stderr=subprocess.PIPE)
        # print(f"File downloaded successfully and saved to {save_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr.decode()}")


def get_audio_length(file_path):
    """
    Get the length of an audio file using ffprobe.

    :param file_path: Path to the audio file.
    :return: Duration of the audio file in seconds.
    """
    command = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {shlex.quote(file_path)}"
    try:
        output = subprocess.check_output(command, shell=True, text=True).strip()
        return float(output)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}", flush=True)
        return None


def download_files(file_list, download_queue):
    for file_url in file_list:
        # print(f"Downloading {file_url}")
        file_ext = file_url.split(".")[-1]
        file_id = str(uuid.uuid4())
        audio_file_name = f"{file_id}.{file_ext}"
        downloaded_file_path = os.path.join(download_dir, audio_file_name)
        wget_download(file_url, downloaded_file_path)
        clip_length = get_audio_length(downloaded_file_path)
        if clip_length is None:
            print(f"{file_url} is invalid")
            continue
        metadata_file_name = f"{file_id}.json"
        metadata_file_path = os.path.join(download_dir, metadata_file_name)
        with open(metadata_file_path, "w") as f:
            json.dump(
                {
                    "file_url": file_url,
                    "downloaded_file_path": downloaded_file_path,
                    "clip_length": clip_length,
                },
                f,
            )
        # Put the path of the downloaded file in the queue
        download_queue.put(metadata_file_path)


def post_files(upload_queue, delete_queue, reporting_queue):
    while True:
        # Get the next file path from the queue
        file_path = upload_queue.get()
        if file_path is None:
            # Sentinel value received, stop the thread
            break

        with open(file_path) as f:
            metadata = json.load(f)

        response = requests.post(
            api_url, json={"url": metadata["downloaded_file_path"]}
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.reason}")
            print(response.text)
            continue

        body = response.json()
        result = {
            "word_count": len(body["text"].split()),
            "audio_url": metadata["file_url"],
        }
        for header in [
            "x-gpu-name",
            "x-salad-machine-id",
            "x-salad-container-group-id",
            "x-processing-time",
            "x-audio-length",
            "x-realtime-factor",
            "x-model-id",
        ]:
            result[header.replace("x-", "")] = response.headers.get(header)

        if metadata["clip_length"]:
            result["audio-length"] = metadata["clip_length"]
            result["realtime-factor"] = metadata["clip_length"] / float(
                response.headers["x-processing-time"]
            )

        # Mark the task as done
        upload_queue.task_done()

        delete_queue.put(file_path)
        reporting_queue.put(result)


def delete_files(delete_queue):
    while True:
        # Get the next file path from the queue
        file_path = delete_queue.get()
        if file_path is None:
            # Sentinel value received, stop the thread
            break

        os.remove(file_path)

        # Mark the task as done
        delete_queue.task_done()


def report_results(reporting_queue):
    while True:
        # Get the next file path from the queue
        result = reporting_queue.get()
        if result is None:
            # Sentinel value received, stop the thread
            break

        if reporting_url == "":
            print(result)
            continue

        requests.post(
            f"{reporting_url}/{benchmark_id}",
            json=result,
            headers=reporting_headers,
        )

        # Mark the task as done
        reporting_queue.task_done()


def wait_for_healthcheck_to_pass():
    max_retries = 100
    tries = 0
    while tries < max_retries:
        tries += 1
        try:
            response = requests.get("http://localhost:8000/hc")
            if response.status_code == 200:
                return
        except Exception as e:
            pass
        time.sleep(1)
    raise Exception("Healthcheck failed")


# List of file URLs to download
with open("all_urls.txt") as f:
    file_list = [line.strip() for line in f]
    random.shuffle(file_list)

# Create a queue
job_queue = queue.Queue()
delete_queue = queue.Queue()
reporting_queue = queue.Queue()

# Create and start the downloader thread
downloader_thread = threading.Thread(target=download_files, args=(file_list, job_queue))
downloader_thread.start()

wait_for_healthcheck_to_pass()

# Create and start the uploader thread
uploader_thread = threading.Thread(
    target=post_files, args=(job_queue, delete_queue, reporting_queue)
)
uploader_thread.start()

deleter_thread = threading.Thread(target=delete_files, args=(delete_queue,))
deleter_thread.start()

reporter_thread = threading.Thread(target=report_results, args=(reporting_queue,))
reporter_thread.start()

# Wait for the downloader thread to finish
downloader_thread.join()

# Once downloading is finished, use a sentinel value to stop the uploader thread
job_queue.put(None)
uploader_thread.join()

delete_queue.put(None)
deleter_thread.join()

reporting_queue.put(None)
reporter_thread.join()

#!/usr/bin/env python3
import cgi
import json
import os
import sys
import traceback

from dotenv import load_dotenv
from webdav3.client import Client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.utils import push_event

params = cgi.parse()
channel_id = params['channel_id'][0]
model_name = params['model_name'][0]

load_dotenv()

options = {
    'webdav_hostname': os.environ.get("WEBDAV_HOST"),
    'webdav_login': os.environ.get("WEBDAV_LOGIN"),
    'webdav_password': os.environ.get("WEBDAV_PASSWORD")
}

client = Client(options)

remote_path = os.environ.get('WEBDAV_PATH')
dataset_path = "Dataset"

result = {}
try:
    if not os.path.exists(dataset_path):
        raise f"Model {model_name} does not exist."
    local_files = []
    remote_files = []
    # retrieve files
    push_event(channel_id, "info", "Retrieving files...")
    for dir in ['anystyle/finder', 'anystyle/parser']:
        # local files
        local_dir = os.path.join(dataset_path, model_name, dir)
        for l in os.listdir(local_dir):
            file_path = os.path.join(local_dir, l)
            local_files.append({"path": file_path,
                                "size": os.path.getsize(file_path),
                                "created": os.path.getctime(file_path),
                                "modified": os.path.getmtime(file_path)
                                })
        # remote files
        remote_dir = os.path.join(remote_path, dataset_path, model_name, dir)
        if client.check(remote_dir):
            remote_files.extend(client.list(remote_dir, get_info=True))
        else:
            client.mkdir(remote_dir)

    # Dataset/zfrsoz/anystyle/finder/10.1515_zfrs-1980-0104.ttx
    # /remote.php/nonshib-webdav/WebDav/CitExt/Dataset/zfrsoz/anystyle/finder/10.1515_zfrs-1985-0205.ttx

    # file_info file
    info_file = '_info.json'
    tmp_info_path = os.path.join("tmp", model_name + info_file)
    with open(tmp_info_path, "w") as f:
        f.write(json.dumps(local_files))
    remote_info_path = os.path.join(remote_path, dataset_path, model_name, info_file)
    if client.check(remote_info_path):
        client.download_sync(remote_info_path, tmp_info_path)
        with open(tmp_info_path, "r") as f:
            remote_info = json.load(f)

    for i, l in enumerate(local_files):
        push_event(channel_id, "info", f"Uploading locally changed files {i+1}/{len(local_files)}")
        rl = [r for r in remote_info if os.path.basename(r['path']) == os.path.basename(l['path'])]
        r = rl[0] if len(rl) > 0 else None
        sys.stderr.write(f"{l['path']}: Remote: {r['modified'] if r else 'none'}, local: {l['modified']}\n")
        if r is None or r['modified'] < l['modified']:
            sys.stderr.write(f"Local is newer, uploading...\n")
            # client.upload_sync(remote_info_path, tmp_info_path)
        elif r['modified'] > l['modified']:
            sys.stderr.write(f"Remote is newer, downloading...\n")
        else:
            sys.stderr.write(f"Local == remote\n")

    client.upload_sync(remote_info_path, tmp_info_path)
    push_event(channel_id, "info", "")

    result["success"] = True
except Exception as err:
    traceback.print_exc()
    result["error"] = str(err)
finally:
    print("Content-Type: application/json\n")
    print(json.dumps(result))

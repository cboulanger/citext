#!/usr/bin/env python3
import cgi
import json
import os
import sys
import traceback

from pathlib import Path
from dotenv import load_dotenv
from webdav3.client import Client

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.sse import SSE, Toast

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
model_path ="Models"

result = {}
local_lock_path = os.path.join(dataset_path, model_name, "lock")
local_lock_created = False
remote_lock_path = os.path.join(remote_path, local_lock_path)
remote_lock_created = False

sse = SSE(channel_id)
toast = Toast(sse, "info", "Synchronizing model data")

def get_local_file_info(model_name, download_missing=False):
    local_file_info = {}
    dir_list = [
        os.path.join(dataset_path, model_name, "anystyle", "finder"),
        os.path.join(dataset_path, model_name, "anystyle", "parser"),
        os.path.join(model_path, model_name)
    ]
    for local_dir in dir_list:
        remote_dir = f"{remote_path}/{local_dir}"

        # download missing remote files
        if client.check(remote_dir):
            if download_missing:
                toast.show("Downloading missing files...")
                client.pull(remote_dir, local_dir)
        else:
            parts = remote_dir.split("/")
            curr_dir = ""
            while len(parts):
                part = parts.pop(0)
                if part:
                    curr_dir += f"/{part}"
                    client.mkdir(curr_dir)

        # make a list of local files, including newly downloaded
        for file_name in os.listdir(local_dir):
            file_path = os.path.join(local_dir, file_name)
            file_info = None
            if file_name.endswith('.deleted'):
                # ignore deleted files
                continue
            elif file_name.endswith(".info"):
                if os.path.exists(file_path[:-5]):
                    # add file info for deleted files,
                    file_info_path = file_path
                    file_path = file_path[:-5]
                else:
                    continue
            else:
                # normal info file
                file_info_path = file_path + ".info"

            # load file info
            if os.path.exists(file_info_path):
                    try:
                        with open(file_info_path) as f:
                            file_info = json.load(f)
                    except:
                        sys.stderr.write(f"Problem parsing {file_info_path}, discarding it...\n")
            if file_info is None:
                file_info = {
                    "modified": os.path.getmtime(file_path),
                    "version": 1
                }
                with open(file_info_path, "w", encoding="utf-8") as f:
                    json.dump(file_info, f)

            local_file_info[file_path] = file_info

    return local_file_info

try:
    if not os.path.exists(dataset_path):
        raise f"Model {model_name} does not exist."

    toast.show("Retrieving version information...")

    # get lock, this has serious race condition issues, but good enough for now
    if client.check(remote_lock_path):
        raise "Remote sync in progress. Try again later."
    if os.path.exists(local_lock_path):
        raise "Local sync in progress. Try again later."
    Path(local_lock_path).touch()
    local_lock_created = True
    client.upload_sync(remote_lock_path,local_lock_path)
    remote_lock_created = True

    # check sync data file
    sync_data_file = '_sync.json'
    remote_sync_data_path = os.path.join(remote_path, dataset_path, model_name, sync_data_file)
    local_sync_data_path  = os.path.join(dataset_path, model_name, sync_data_file)

    # download remote sync data if exists
    if client.check(remote_sync_data_path):
        client.download_sync(remote_sync_data_path, local_sync_data_path)
        with open(local_sync_data_path, "r") as f:
            remote_sync_data = json.load(f)
    else:
        remote_sync_data = {
            "files": {}
        }

    # create local sync data or create it
    local_file_info = get_local_file_info(model_name)
    num_updated_locally = 0
    num_updated_remotely = 0
    local_files = local_file_info.keys()
    num_files = len(local_files)
    for i, local_file_path in enumerate(local_files):
        l = local_file_info[local_file_path]
        remote_file_path = f"{remote_path}/{local_file_path}"
        local_file_info_path = local_file_path + '.info'
        remote_file_info_path = remote_file_path + '.info'
        file_name = os.path.basename(local_file_path)
        # find corresponding entry in remote files
        if local_file_path in remote_sync_data['files'].keys():
            r = remote_sync_data['files'][local_file_path]
            # sys.stderr.write(f"{local_file_path}: Remote: {r['version']}, local: {l['version']}\n")
            if 'deleted' in r and not 'deleted' in l:
                toast.show(f"Deleting {file_name} here ({i + 1}/{num_files})")
                sys.stderr.write(f"{local_file_path}: Was deleted on server, deleting (renaming) here, too...\n")
                try:
                    deleted_file_path = f"{file_path}.deleted"
                    os.remove(deleted_file_path) if os.path.exists(deleted_file_path)
                    os.rename(file_path, deleted_file_path)
                except Exception as e:
                    sys.stderr.write(f"{local_file_path}: Problem renaming: {str(e)} ...\n")
                l['deleted'] = true
            elif 'deleted' in l and not 'deleted' in r:
                toast.show(f"Deleting {file_name} on server ({i + 1}/{num_files})")
                sys.stderr.write(f"{local_file_path}: Was deleted here, deleting on server, too...\n")
                try:
                    client.clean(remote_file_path)
                    #client.clean(remote_file_info_path)
                except Exception as e:
                    sys.stderr.write(f"{local_file_path}: Problem deleting on server: {str(e)}.\n")
            elif 'version' not in r or r['version'] < l['version']:
                toast.show(f"Uploading {file_name} ({i + 1}/{num_files})")
                sys.stderr.write(f"{local_file_path}: Local file is newer, uploading...\n")
                num_updated_remotely += 1
                client.upload_sync(remote_file_path, local_file_path)
                client.upload_sync(remote_file_info_path, local_file_info_path)
            elif r['version'] > l['version']:
                toast.show(f"Downloading {file_name} ({i + 1}/{num_files})")
                sys.stderr.write(f"{local_file_path}: Remote file is newer, downloading...\n")
                client.download_sync(remote_file_path, local_file_path)
                l['version'] = r['version']
                l['modified'] = r['modified']
                num_updated_locally += 1
                with open(local_file_info_path, "w", encoding="utf-8") as f:
                    json.dump(l, f)
            # else:
            #    sys.stderr.write(f"Local == remote\n")
        else:
            if 'deleted' in l:
                sys.stderr.write(f"{local_file_path}: Deleted locally, not uploading...\n")
            else:
                toast.show(f"Uploading {file_name} ({i + 1}/{num_files})")
                sys.stderr.write(f"{local_file_path}: Remote file is missing, uploading...\n")
                num_updated_remotely += 1
                client.upload_sync(remote_file_path, local_file_path)
                client.upload_sync(remote_file_info_path, local_file_info_path)

    # update sync data
    local_sync_data = {
        "files": local_file_info
    }
    with open(local_sync_data_path, "w", encoding="utf-8") as f:
        json.dump(local_sync_data, f)
    if num_updated_remotely > 0:
        sys.stderr.write(f"Updating remote sync data...\n")
        client.upload_sync(remote_sync_data_path, local_sync_data_path)

    toast.close()
    Toast(sse,"success", "Synchronization finished")\
        .show(f"Updated {num_updated_locally} files here and {num_updated_remotely} on server.")

    result["success"] = True
except Exception as err:
    traceback.print_exc()
    result["error"] = str(err)
finally:
    toast.close()
    if local_lock_created:
        os.remove(local_lock_path)
    if remote_lock_created:
        client.clean(remote_lock_path)
    print("Content-Type: application/json\n")
    print(json.dumps(result))

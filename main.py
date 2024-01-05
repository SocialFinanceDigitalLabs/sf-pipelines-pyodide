import io
import os
import zipfile

import js
from pyodide.ffi.wrappers import add_event_listener
from pyodide.ffi import to_js
from fs import open_fs

from sf_pipelines_test.ssda903_pipeline.pipeline import process_session

home_fs = open_fs("~/")
source_dir = "source"
target_dir = "target"
home_fs.makedirs(source_dir)
home_fs.makedirs(target_dir)


async def process_files(e):
    log("started processing files...")
    file_list = e.target.files
    await dump_files(file_list, source_dir)
    log(f"dumped {len(file_list)} file to source directory: {source_dir}")
    log("processing files throught the clean pipeline...")

    source_fs = open_fs(source_dir)
    target_fs = open_fs(target_dir)
    process_session(source_fs, target_fs, "CAM")

    log(f"processed {len(file_list)} to {target_dir}")

    content = dir_to_zip(target_dir)

    log("exporting zip file...")
    js.exportZip(to_js(content))
    log("done!")


async def dump_files(files, directory):
    for file in files:
        file_bytes: bytes = await get_bytes_from_file(file)
        with open(f"{directory}/{file.name}", "wb") as f:
            f.write(file_bytes)


async def get_bytes_from_file(file):
    array_buf = await file.arrayBuffer()
    return array_buf.to_bytes()


def dir_to_zip(source_dir):
    log(f"zipping {source_dir} directory...")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, source_dir))
    return zip_buffer.getvalue()


def log(message):
    # log to pandas dev console
    print(message)
    # log to JS console
    js.console.log(message)


add_event_listener(js.document.getElementById("files"), "change", process_files)
log("waiting for files to be uploaded...")

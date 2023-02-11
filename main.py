import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from google.cloud import storage
from google.cloud import vision
from models import Parking
from send_pushover import send_pushover

from orm import access_table
from typing import Union

from pydantic import BaseModel


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bsid-user-group5-sa-key.json"
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage_client = storage.Client()


@app.get("/")
def hello_world():
    return {"Hello": "World"}


@app.get("/buckets/{bucket}/blobs")
def list_blobs_by_bucket(bucket):
    """Lists all the blobs in the bucket."""
    return [blob.name for blob in storage_client.list_blobs(bucket)]


# Use FileResponse to return the file
@app.get("/buckets/{bucket}/{folder}/{file}")
def return_image_from_bucket(bucket: str, folder: str, file: str):
    # Determine download_path
    if not file.endswith(".jpg"):
        file = file + ".jpg"
    download_path = f"/root/adslXmlad/images/{file}"
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    # Download file
    if not os.path.exists(download_path):
        blob = storage_client.get_bucket(bucket).blob(f"{folder}/{file}")
        blob.download_to_filename(download_path)

    # download_path = f"gs://{bucket}/{folder}/{file}" # Can't support this

    return FileResponse(download_path)


@app.get("/license_time/{license_plate}/{current_time}")
def return_parking_number(license_plate: str, current_time: int):
    parking_history = [
        entry
        for entry in access_table("query", "entry_records")
        if license_plate == entry["license_plate"]
    ]
    for entry in parking_history:
        if (
            entry["entry_time"].total_seconds()
            <= current_time
            <= entry["exit_time"].total_seconds()
        ):
            return entry["parking_number"]
    return None
    return parking_history


@app.get("/image/{parking_number}/{entry_time}")
def return_image_from_public(parking_number: str, entry_time: int):
    # Get file name using parking_number and entry_time
    bucket = "tsmchack2023-bsid-grp5-public-read-bucket"
    folder = "public_scenario_images"
    file = None
    filename_list = [blob.name for blob in storage_client.list_blobs(bucket)]
    for filename in filename_list:
        if f"{parking_number}_{entry_time:04d}" in filename:
            file = filename.split("/")[-1]
            break
    if file is None:
        return {"result": "File not found"}

    # Determine download_path
    download_path = f"/root/adslXmlad/images/{file}"
    # return download_path
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    # Download file
    if not os.path.exists(download_path):
        blob = storage_client.get_bucket(bucket).blob(f"{folder}/{file}")
        blob.download_to_filename(download_path)

    # download_path = f"gs://{bucket}/{folder}/{file}" # Can't support this

    return FileResponse(download_path)


@app.get("/image/{parking_number}/{entry_time}/vision")
def return_image_vision_from_public(parking_number: str, entry_time: int):
    # Get file name using parking_number and entry_time
    bucket = "tsmchack2023-bsid-grp5-public-read-bucket"
    folder = "public_scenario_images"
    file = None
    filename_list = [blob.name for blob in storage_client.list_blobs(bucket)]
    for filename in filename_list:
        if f"{parking_number}_{entry_time:04d}" in filename:
            file = filename.split("/")[-1]
            break
    if file is None:
        return {"result": "File not found"}

    # Get vision result
    return get_vision(bucket, folder, file)


@app.get("/vision/{bucket}/{folder}/{file}")
def get_vision(bucket: str, folder: str, file: str):
    image_uri = f"gs://{bucket}/{folder}/{file}"
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = image_uri
    response = client.text_detection(image=image)
    r = response.text_annotations[0].description
    return {"vision_result": r}


@app.get("/{mode}/{table}/")
def access_table_api(
    mode: str,
    table: str,
    license_plate=None,
    entry_time=None,
    exit_time=None,
    eff_start_time=None,
    eff_end_time=None,
    parking_number=None,
):
    data = {}
    if license_plate:
        data["license_plate"] = license_plate
    if entry_time:
        data["entry_time"] = entry_time
    if exit_time:
        data["exit_time"] = exit_time
    if eff_start_time:
        data["eff_start_time"] = eff_start_time
    if eff_end_time:
        data["eff_end_time"] = eff_end_time
    if parking_number:
        data["parking_number"] = parking_number
    # return data
    return access_table(mode, table, data)


# Pushover API
@app.get("/pushover/{msg}")
def send_pushover_api(msg: str):
    send_pushover(msg)

    return {"result": "success"}


@app.get("/parking/{parking_number}")
def get_parking_number_history(parking_number: str):
    parking_history = [
        entry
        for entry in access_table("query", "entry_records")
        if parking_number == entry["parking_number"]
    ]
    color = (
        "red"
        if len(parking_history) > 0
        and parking_history[-1]["exit_time"].total_seconds() == 1439
        else "green"
    )
    return {"parking_history": parking_history, "color": color}


# run server
# uvicorn main:app --reload --host 0.0.0.0 --port 8000

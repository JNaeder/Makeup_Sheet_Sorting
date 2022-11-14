import json
import os
import re
from google.cloud import storage, vision
from google.oauth2 import service_account

raw_folder = "/Users/johnnaeder/Google Drive/Shared drives/NY Tech Drive/Makeup Sheets Stuff/RAW"
raw_files = os.listdir(raw_folder)

gcs_source_uri = "gs://makeup_sheet_raw/2337_001.pdf"
gcs_destination_uri = "gs://makeup_sheet_sorted/pdf_result"

credentials = service_account.Credentials.from_service_account_file("google_credentials.json")
storage_client = storage.Client(credentials=credentials)
bucket = storage_client.bucket("makeup_sheet_raw")

# for file in raw_files:
#     blob = bucket.blob(file)
#     full_path = raw_folder + "/" + file
#     # blob.upload_from_filename(full_path)
#     print(f"Uploaded {file}")

mime_type = 'application/pdf'
batch_size = 2
client = vision.ImageAnnotatorClient(credentials=credentials)
feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

gcs_source = vision.GcsSource(uri=gcs_source_uri)
input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
output_config = vision.OutputConfig(gcs_destination=gcs_destination, batch_size=batch_size)

async_request = vision.AsyncAnnotateFileRequest(features=[feature], input_config=input_config,
                                                output_config=output_config)
operation = client.async_batch_annotate_files(requests=[async_request])
operation.result(timeout=420)

match = re.match(r'gs://([^/]+)/(.+)', gcs_destination_uri)
bucket_name = match.group(1)
prefix = match.group(2)
output_bucket = storage_client.bucket(bucket_name)

blob_list = list(output_bucket.list_blobs(prefix=prefix))
output = blob_list[0]

json_string = output.download_as_string()
response = json.loads(json_string)

first_page = response["responses"][0]
text_annotation = first_page['fullTextAnnotation']

print(text_annotation)


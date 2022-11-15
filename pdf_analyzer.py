import json
import os
import re
from google.cloud import storage, vision
from google.oauth2 import service_account
from PyPDF2 import PdfFileReader, PdfFileWriter

raw_folder = "/Users/johnnaeder/Google Drive/Shared drives/NY Tech Drive/Makeup Sheets Stuff/RAW"
raw_files = os.listdir(raw_folder)


class PDF_Manager:
    def __init__(self):
        self._gcs_source_uri_path = "gs://makeup_sheet_raw/"
        self._gcs_destination_uri = "gs://makeup_sheet_sorted/pdf_result"

        self._credentials = service_account.Credentials.from_service_account_file("google_credentials.json")
        self._storage_client = storage.Client(credentials=self._credentials)
        self._raw_bucket = self._storage_client.bucket("makeup_sheet_raw")
        self._sorted_bucket = self._storage_client.bucket("makeup_sheet_sorted")

    def pdf_uploader(self, full_file_path, file_name):
        """ Uploads files to the RAW storage bucket"""
        blob = self._raw_bucket.blob(file_name)
        blob.upload_from_filename(full_file_path)
        print(f"Uploaded {file_name}")

    def delete_pdfs_from_buckets(self):
        all_buckets = self._storage_client.list_buckets()
        for bucket in all_buckets:
            all_blobs = bucket.list_blobs()
            for blob in all_blobs:
                blob.delete()

    def pdf_analyzer(self, file_name):

        mime_type = 'application/pdf'
        batch_size = 2
        client = vision.ImageAnnotatorClient(credentials=self._credentials)
        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

        gcs_source_uri = self._gcs_source_uri_path + "/" + file_name
        gcs_source = vision.GcsSource(uri=gcs_source_uri)
        input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

        gcs_destination = vision.GcsDestination(uri=self._gcs_destination_uri)
        output_config = vision.OutputConfig(gcs_destination=gcs_destination, batch_size=batch_size)

        async_request = vision.AsyncAnnotateFileRequest(features=[feature], input_config=input_config,
                                                        output_config=output_config)
        operation = client.async_batch_annotate_files(requests=[async_request])
        operation.result(timeout=420)

        match = re.match(r'gs://([^/]+)/(.+)', self._gcs_destination_uri)
        bucket_name = match.group(1)
        prefix = match.group(2)
        output_bucket = self._storage_client.bucket(bucket_name)

        blob_list = list(output_bucket.list_blobs(prefix=prefix))

        output = []
        for i in range(len(blob_list)):
            blob = blob_list[i]

            json_string = blob.download_as_string()
            response = json.loads(json_string)

            first_page = response["responses"][0]
            text_annotation = first_page['fullTextAnnotation']

            output.append(text_annotation)
        return output


pdf_manager = PDF_Manager()

from google.cloud import storage
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def download_blob(bucket_name, source_blob_name, destination_file_name):
    source_blob_name = f'templates/{source_blob_name}'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    return logging.info(f"Downloadblob latasi bucketista kortin {source_blob_name} lokaalia käsittelyä varten")
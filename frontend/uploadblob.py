from google.cloud import storage
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def uploadaa_template(bucket_name, source_file_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    return logging.info(f"Upload_blob uploadasi templaten {source_file_name} bucketiin {bucket_name}. Pathi: {destination_blob_name}")

def uploadaa_postikortti_jpg(bucket_name, source_file_name, destination_blob_name):
    destination_blob_name = f'jpg/{destination_blob_name}'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    return logging.info(f"Upload_blob uploadasi jpg-kortin {source_file_name} bucketiin {bucket_name}. Pathi: {destination_blob_name}")

def uploadaa_postikortti_html(bucket_name, source_file_name, destination_blob_name):
    destination_blob_name = f'html/{destination_blob_name}'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    return logging.info(f"Upload_blob uploadasi html-kortin {source_file_name} bucketiin {bucket_name}. Pathi: {destination_blob_name}")
from google.cloud import secretmanager
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def access_secret_version(project_id, secret_id, version_id):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        return payload
    except RuntimeError as err:
        print(err)
        return logging.error(f"Secretsconfigin access_secret_version failasi (ongelma yhteydessä GCP:hen)")
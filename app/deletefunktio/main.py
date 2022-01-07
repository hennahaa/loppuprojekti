# TO DO: Lisää origin-url (frontin url) riveille 19, 29

import psycopg2
from google.cloud import secretmanager
import json, os
    
def poistatoken(request):
    """Poistaa e-korttitokenin tietokannasta, trigger-json frontin JavaScriptistä.
    CORS-osuus lainattu Googlen omasta dokumentaatiosta: https://cloud.google.com/functions/docs/samples/functions-http-cors#functions_http_cors-python"""
    
    # For more information about CORS and CORS preflight requests, see:
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows POST requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': 'frontin-url-tähän',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
            'Access-Control-Allow-Credentials': 'true'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': 'frontin-url-tähän',
        'Access-Control-Allow-Credentials': 'true',
        'Vary': 'Origin'
    }

    request_json = request.get_json(silent=True)
    token = request_json.get("token")

    # haetaan Secret Managerista tietokannan speksit, ympäristömuuttujasta GCP project ID
    client = secretmanager.SecretManagerServiceClient()
    
    project_id = os.environ.get('PROJECTID')
    
    path_dbname = "projects/{}/secrets/{}/versions/{}".format(project_id, 'kekkoslovakia-db-name', 'latest')
    encr_dbname = client.access_secret_version(request={"name": path_dbname})
    dbname = encr_dbname.payload.data.decode("UTF-8")

    path_username = "projects/{}/secrets/{}/versions/{}".format(project_id, 'kekkoslovakia-db-user', 'latest')
    encr_user = client.access_secret_version(request={"name": path_username})
    user = encr_user.payload.data.decode("UTF-8")
    
    path_password = "projects/{}/secrets/{}/versions/{}".format(project_id, 'kekkoslovakia-db-srv-pw', 'latest')    
    encr_password = client.access_secret_version(request={"name": path_password})
    password = encr_password.payload.data.decode("UTF-8")

    host = '34.88.169.103' # host url on aina sama, joten olkoon julkinen
    
    # otetaan yhteys tietokantaan, poistetaan triggeristä saatu token-arvo tietokannasta
    con = None
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cursor = con.cursor()
        
        SQL = '''UPDATE linkit SET token = NULL WHERE token = %s;'''
        cursor.execute(SQL, (token,))
        con.commit()
                
        cursor.close()
        print('Token deleted.', 200, headers)
        return ('Token deleted.', 200, headers)

    except (Exception,psycopg2.DatabaseError) as error:
        print(error)
        return 'Something went wrong'
# TO DO: Lisää origin-url (frontin url) riveille 19, 29

import psycopg2
from google.cloud import secretmanager
import os
    
def poistatoken(request):
    """Poistaa e-korttitokenin tietokannasta, trigger-json frontin JavaScriptistä.
    CORS-osuus lainattu Googlen omasta dokumentaatiosta: https://cloud.google.com/functions/docs/samples/functions-http-cors#functions_http_cors-python"""

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows POST requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': 'https://korttigeneraattori-testi-7a6ps2xuoq-lz.a.run.app',
            'Access-Control-Allow-Methods': 'DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
            'Access-Control-Allow-Credentials': 'true'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': 'https://korttigeneraattori-testi-7a6ps2xuoq-lz.a.run.app',
        'Access-Control-Allow-Credentials': 'true',
        'Vary': 'Origin'
    }

    request_json = request.get_json(silent=True)

    if request.args and 'token' in request.args:
        token = int(request.args.get('token'))
    elif request_json and 'token' in request_json:
        token = int(request_json['token'])
    else:
        #palauttaa virheen jos tokenia ei syötetä
        token = 0

    # haetaan Secret Managerista tietokannan speksit, ympäristömuuttujasta GCP project ID
    client = secretmanager.SecretManagerServiceClient()
    
    PROJECT_ID = os.environ.get('PROJECTID')
    
    path_dbname = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-name', 'latest')
    encr_dbname = client.access_secret_version(request={"name": path_dbname})
    dbname = encr_dbname.payload.data.decode("UTF-8")

    path_username = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-user', 'latest')
    encr_user = client.access_secret_version(request={"name": path_username})
    user = encr_user.payload.data.decode("UTF-8")
    
    path_password = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-srv-pw', 'latest')    
    encr_password = client.access_secret_version(request={"name": path_password})
    password = encr_password.payload.data.decode("UTF-8")

    path_host = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-ip', 'latest')
    encr_host = client.access_secret_version(request={"name": path_host})
    host = encr_host.payload.data.decode("UTF-8")
    
    # otetaan yhteys tietokantaan, poistetaan triggeristä saatu token-arvo tietokannasta
    con = None
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cursor = con.cursor()
        
        SQL = '''UPDATE tokenilinkit SET tokeni = NULL WHERE tokeni = %s;'''
        cursor.execute(SQL, (token,))
        con.commit()
                
        cursor.close()
        print('Token deleted.', 200, headers)
        return ('Token deleted.', 200, headers)

    except (Exception,psycopg2.DatabaseError) as error:
        print(error)
        return 'Something went wrong'
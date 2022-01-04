# TO DO: tietokannan speksit haettava salaisuuksista kovakoodauksen sijasta

import psycopg2
from google.cloud import secretmanager
import json, os
    
def poistatoken(request):
    """Poistaa e-korttitokenin tietokannasta, trigger frontin JavaScriptistä"""
    
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

        request_json = request.get_json(silent=True)
        token = request_json.get("token")
        
        SQL = '''UPDATE linkit SET token = NULL WHERE token = %s;'''
        cursor.execute(SQL, (token,))
        con.commit()
                
        cursor.close()
        return 'Token deleted.'

    except (Exception,psycopg2.DatabaseError) as error:
        print(error)
        return 'Something went wrong'
import psycopg2
import os
from google.cloud import secretmanager

def hae_kaikki_kortit(request):

    client = secretmanager.SecretManagerServiceClient()
    PROJECT_ID = os.environ.get('PROJECT_ID')
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

    con = None
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cursor = con.cursor()
        SQL = '''SELECT html_bucketissa FROM tokenilinkit;'''
        print(SQL)
        cursor.execute(SQL)
        result = cursor.fetchall()
        url = []
        if len(result) >=1:
            for i in result:
                url.append(i[0])
                print(url)
            s = ', '.join(map(str, url))
            cursor.close()
            return s
        else:
            cursor.close()
            return "Tietokannassa ei ole kortteja."
        
    except (Exception,psycopg2.DatabaseError) as error:
        return 'Haku ei onnistunut!'   
    
    finally:
        if con is not None:
            con.close()
import psycopg2
import os
import json 
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

    host = '34.88.169.103'
    con = None
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cursor = con.cursor()
        SQL = '''SELECT * FROM links;'''
        cursor.execute(SQL)
        result = cursor.fetchall()
        url = []
        if len(result) >=1:
            print("korttien lukumäärä: ", len(result))
            for i in result:
                url.append(i[1])
            s = ', '.join(map(str, url))
            return s
        else:
            return "Tietokannassa ei ole kortteja."
        cursor.close()
    except (Exception,psycopg2.DatabaseError) as error:
        return 'Jokin meni pieleen.'   
    
    finally:
        if con is not None:
            con.close()

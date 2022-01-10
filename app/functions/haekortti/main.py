import psycopg2
import os
from google.cloud import secretmanager


def hae_kortti(request):

    request_json = request.get_json(silent=True)

    if request.args and 'id' in request.args:
        id = int(request.args.get('id'))
    elif request_json and 'id' in request_json:
        id = int(request_json['id'])
    else:
        #palauttaa virheen jos id:tä ei syötetä
        id = 0

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
    
    con = None  
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cursor = con.cursor()
        try:
            #hakee nyt yksittäisen kortin url:än
            SQL = '''SELECT html_bucketissa FROM tokenilinkit WHERE id = 1;'''
            print(SQL)
            cursor.execute(SQL, (id,))
            row = cursor.fetchall()
            url = row[0][0]
            cursor.close()
            return url
            
        except (Exception,psycopg2.DatabaseError) as error:
            cursor.close()
            return "Valitsemallasi id:llä ei löytynyt korttia"
        
        
    except (Exception,psycopg2.DatabaseError) as error:
        return error
    finally:
        if con is not None:
            con.close()
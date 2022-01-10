import string, random, datetime, json, os
import psycopg2
from google.cloud import storage, secretmanager

#copypastesin tähä vaan ton hae_kortti_urlin koodin näin alkuun

def lisaa_kortti():

    #client = secretmanager.SecretManagerServiceClient()
    #PROJECT_ID = os.environ.get('PROJECTID')
    #path_dbname = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-name', 'latest')
    #encr_dbname = client.access_secret_version(request={"name": path_dbname})
    #dbname = encr_dbname.payload.data.decode("UTF-8")

    #path_username = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-user', 'latest')
    #encr_user = client.access_secret_version(request={"name": path_username})
    #user = encr_user.payload.data.decode("UTF-8")
    
    #path_password = "projects/{}/secrets/{}/versions/{}".format(PROJECT_ID, 'kekkoslovakia-db-srv-pw', 'latest')    
    #encr_password = client.access_secret_version(request={"name": path_password})
    #password = encr_password.payload.data.decode("UTF-8")

    #host = '34.88.169.103'
    con = None  
    try:
        con = psycopg2.connect(database="postgres", user="postgres", password="ft6r6Ezwpy0mvmH0", host="34.88.169.103")
        cursor = con.cursor()
        #request_json = request.get_json(silent=True)
        #id = request_json['id']
        try:
            #testiä
            SQL = '''SELECT * FROM links;'''
            cursor.execute(SQL)
            row = cursor.fetchall()
            print(row)
            url = row[0][1]
            cursor.close()
            return "lol testi!"
            #return url
            
        except (Exception,psycopg2.DatabaseError) as error:
            cursor.close()
            return "Valitsemallasi id:llä ei löytynyt korttia"
        
        
    except (Exception,psycopg2.DatabaseError) as error:
        return error
    finally:
        if con is not None:
            con.close()

print(lisaa_kortti())
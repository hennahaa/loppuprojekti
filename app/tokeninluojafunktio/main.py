# TO DO 1: Signed URL!
# TO DO 2: Siivoa, jaa pienempiin funktioihin...

import string, random, datetime, json, os
import psycopg2
from google.cloud import storage, secretmanager

def event_tietokantaan(event):
    """HTTP-funktio, joka käsittelee frontin lomakkeesta tulevaa json-dataa ja lisää tietokantaan.
    Hakee ympäristömuuttujasta project ID:n."""

    event_json = event.get_json(silent=True)
    bucket_name = event_json.get("bucket")
    object_name = event_json.get("name")
    email = event_json.get("email")
    token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15))

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    url = 'https://storage.cloud.google.com/{}/{}'.format(bucket_name,object_name)
    signed_url = blob.generate_signed_url(
        version="v4",
        # URL on voimassa 7 vrk
        expiration=datetime.timedelta(seconds=604800),
        # sallitaan GET requestit
        method="GET",
    )

    # haetaan Secret Managerista tietokannan speksit ja ympäristömuuttujasta project ID
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

    host = '34.88.169.103' #host url on aina sama, joten olkoon julkinen
    
    # otetaan yhteys tietokantaan, lisätään requestista saadut arvot tietokantaan
    con = None
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cursor = con.cursor()
        SQL = '''INSERT INTO linkit VALUES (%s,%s,%s,%s);'''
        values = (token, url, signed_url, email)
        cursor.execute(SQL, values)
        con.commit()
        cursor.close()
        return "Database updated."
    except (Exception,psycopg2.DatabaseError) as error:
        print(error)
        return "Could not connect to the database."
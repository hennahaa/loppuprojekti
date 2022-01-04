#TO DO: tietokantayhteyskonffaus

import string, random
import psycopg2
from google.cloud import storage
import datetime

def event_tietokantaan(event):
    """HTTPS-funktio, joka käsittelee frontin lomakkeesta tulevaa dataa ja lisää tietokantaan.
    Args:
        event (dict):  The dictionary with data specific to this type of event.
                       The `data` field contains a description of the event in
                       the Cloud Storage `object` format described here:
                       https://cloud.google.com/storage/docs/json_api/v1/objects#resource"""

    token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15))
    bucket_name = event['bucket']
    object_name = event['name']
    vastaanottajan_meili = event['email']

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    url = blob.generate_signed_url(
        version="v4",
        # URL on voimassa 7 vrk
        expiration=datetime.timedelta(seconds=604800),
        # sallitaan GET requestit
        method="GET",
    )

    # otetaan yhteys tietokantaan
    con = None
    try:
        con = psycopg2.connect('dbname= user= password= host=')
    except (Exception,psycopg2.DatabaseError) as error:
        print(error, "Ei saatu yhteyttä tietokantaan.")

    cursor = con.cursor()
    SQL = '''INSERT INTO #tablename VALUES (%s,%s,%s);'''
    cursor.execute(SQL, url, token, vastaanottajan_meili)
    con.commit()
    print("Tietokanta päivitetty.")
    cursor.close()
    
    if con is not None:
            con.close()
#TO DO: vastaanottajan meilin hakeminen (rivi 20), miten, mistä, häh?
#TO DO: tietokantaconffaus (rivi 25), haetaan Secret Managerista

import string, random
import psycopg2

def luo_token_ja_url(event, context):
    """Lisää tietokantaan e-korttikuvatiedoston bucket-url:in ja satunnaisen 15-merkkisen tokenin
    Args:
        event (dict):  The dictionary with data specific to this type of event.
                       The `data` field contains a description of the event in
                       the Cloud Storage `object` format described here:
                       https://cloud.google.com/storage/docs/json_api/v1/objects#resource
        context (google.cloud.functions.Context): Metadata of triggering event."""

    token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15))
    bucket_name = event['bucket']
    object_name = event['name']
    object_url = 'https://storage.cloud.google.com/{}/{}'.format(bucket_name,object_name)
    vastaanottajan_meili = ''

    # otetaan yhteys tietokantaan
    con = None
    try:
        con = psycopg2.connect('dbname= user= password= host=')
        return con
    except (Exception,psycopg2.DatabaseError) as error:
        print(error, "Could not connect to database.")

    cursor = con.cursor()
    SQL = '''INSERT INTO #tablename() VALUES (%s,%s,%s);'''
    cursor.execute(SQL, object_url, token, vastaanottajan_meili)
    con.commit()
    print(f"Tietokanta päivitetty.")
    cursor.close()
    
    if con is not None:
            con.close()    
        
import string, random, datetime, json, os, logging
import psycopg2
from google.cloud import storage, secretmanager

def event_tietokantaan(event):
    """HTTP-funktio, joka käsittelee frontin lomakkeesta tulevaa json-dataa ja lisää tietokantaan.
    Hakee ympäristömuuttujasta project ID:n."""
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO) # loggaa kaikki infotasosta ylöspäin olevat viestit

    # käsittelee datan tilausjonoa varten
    event_json = event.get_json(silent=True)
    final_template_nimi = event_json.get("final_template_nimi")
    final_saajan_nimi = event_json.get("final_saajan_nimi")
    final_saajan_sposti = event_json.get("final_saajan_sposti")
    final_lahet_nimi = event_json.get("final_lahet_nimi")
    final_lahet_viesti = event_json.get("final_lahet_nimi")
    final_kuva = event_json.get("final_kuva")
    final_youtube = event_json.get("final_youtube")

    # viestin pituuden haku data-analyysia varten
    viestinpituus = len(final_lahet_viesti)

    # muodostetaan token, joka koostuu 15 satunnaisesta pikkukirjaimesta
    tokeni = ''.join(random.choice(string.ascii_lowercase) for _ in range(15))
    buckettiin_tiedostonnimi = final_kuva[5:]
    randomtiedostonnimi = ''.join(random.choice(string.ascii_lowercase) for i in range(8)) + ".html"
    kortti_jpg_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/jpg/{buckettiin_tiedostonnimi}"
    kortti_html_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/html/{randomtiedostonnimi}"
    
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

    path_host = "projects/{}/secrets/{}/versions/{}".format(project_id, 'kekkoslovakia-db-ip', 'latest')
    encr_host = client.access_secret_version(request={"name": path_host})
    host = encr_host.payload.data.decode("UTF-8")
    
    # otetaan yhteys tietokantaan, lisätään requestista saadut arvot tietokantaan
    con = None
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO tilausjono (template_nimi, saajan_nimi, saajan_sposti, lahet_nimi, lahet_viesti, viest_pituus, final_kuva, final_youtube, html_sivu)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """,
            (final_template_nimi,final_saajan_nimi,final_saajan_sposti,final_lahet_nimi,final_lahet_viesti,viestinpituus,final_kuva,final_youtube,randomtiedostonnimi))
        cur.execute("""
            INSERT INTO tokenilinkit (tokeni, jpg_bucketissa, html_bucketissa, html_tiedosto)
            VALUES (%s,%s,%s,%s);
            """,
            (tokeni,kortti_jpg_tiedostourl_bucketissa,kortti_html_tiedostourl_bucketissa,randomtiedostonnimi))
        con.commit()
        logging.info(f'Frontin käyttäjä on onnistuneesti lähettänyt kortin tilausjonoon. Saaja: {final_saajan_sposti}, JPG url: {kortti_jpg_tiedostourl_bucketissa}, HTML url: {kortti_html_tiedostourl_bucketissa}')

        return "Database updated."
    except (Exception, psycopg2.DatabaseError) as err:
        logging.error(f'Frontin käyttäjä epäonnistui kortin lähettämisessä tilausjonoon, sillä ohjelmassa tapahtui virhe')
        logging.error(err)
        return "Something went wrong."
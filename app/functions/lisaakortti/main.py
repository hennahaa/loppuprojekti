# TO DO: oikea ämpärin nimi (nyt Tiinan oma testiämpäri kovakoodattuna sinne sun tänne + kekkoslovakia-cards)
# TO DO: JavaScript-pätkä html:än VAI erillinen .js-tiedosto?
# TO DO: testaus frontin kautta?
from google.cloud import storage, secretmanager
import json, logging, os, random, string, psycopg2

def lisaa_postikortti(request):
    """Lisää korttikuvatiedoston buckettiin. Luo html-sivun ja lisää sen toiseen buckettiin.
    Request tulee .json-muodossa frontista."""
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    request_json = request.get_json(silent=True)
    final_template_nimi = request_json.get['final_template_nimi']
    final_saajan_nimi = request_json.get['final_saajan_nimi']
    final_saajan_sposti = request_json.get['final_saajan_sposti']
    final_lahet_nimi = request_json.get['final_lahet_nimi']
    final_lahet_viesti = request_json.get['final_lahet_viesti']
    final_kuva = request_json.get['final_kuva']
    final_youtube = request_json.get['final_youtube']
    # parsetaan youtube-linkki samantien
    final_youtube = final_youtube[-11:]
    # viestin pituuden haku data-analyysiä varten
    viestinpituus = len(final_lahet_viesti)
    
    # haetaan Cloud Storagen speksit
    storage_client = storage.Client()
    bucket_name = storage_client.bucket("tiinan-testiampari-1")
    
    # tallennetaan kuvatiedosto buckettiin
    buckettiin_tiedostonnimi = final_kuva[5:]
    pathi_mista_haetaan = f"static/temp/{buckettiin_tiedostonnimi}"
    jpg_buckettiin(bucket_name, buckettiin_tiedostonnimi, pathi_mista_haetaan)

    kortti_jpg_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/jpg/{buckettiin_tiedostonnimi}"
    
    # muodostetaan token, joka koostuu 15 satunnaisesta pikkukirjaimesta
    tokeni = ''.join(random.choice(string.ascii_lowercase) for _ in range(15))

    # kirjoitetaan html-tiedosto ja tallennetaan oikeaan buckettiin
    randomstringi = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    randomtiedostonnimi = randomstringi + ".html"
    
    try:
        path = f"html/{randomtiedostonnimi}"
        blob = storage.Blob(
            name=path,
            bucket=bucket_name
        )
          
        html_sivu = luo_html_sivu(kortti_jpg_tiedostourl_bucketissa, final_youtube)
        
        blob.upload_from_string(
            data=html_sivu,
            content_type='text/plain',
            client=storage_client,
        )
        logging.info(f'Luotiin html-tiedosto: {randomtiedostonnimi}.')

    except RuntimeError as err:
        print(err)
        return logging.error(f"HTML-tiedoston luominen epäonnistui.")

    kortti_html_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/html/{randomtiedostonnimi}"

    con = tietokantayhteys()
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


def jpg_buckettiin(bucket_name, tiedostonnimi, pathi):
    try:
        destination_blob_name = f'jpg/{tiedostonnimi}'
        bucket = bucket_name
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(pathi)
        return logging.info(f"Kortti ladattu. Pathi: {destination_blob_name}")
    except RuntimeError as err:
        print(err)
        return logging.error(f"Postikorttikuvatiedoston lataaminen epäonnistui (ongelma yhteydessä GCP:hen)")


def luo_html_sivu(jpg_url, youtube):
    sivu = f"""<!DOCTYPE html> 
    <html lang="fi"> 
    <head> 
    <title>Kortti sinulle!</title> 
    <meta charset="utf-8"> 
    <meta name="viewport" content="width=device-width, initial-scale=1"> 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"> 
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 80%22><text y=%22.9em%22 font-size=%2280%22>✉️</text></svg>"> 
    </head> 
    <body> 
    <center> 
    <br><h3>Olet saanut e-postikortin!</h3><br> 
    <img class="img-fluid" src="{jpg_url}"><br> 
    <br><p>Lähettäjä halusi lisätä kortin yhteydeen oman audioraidan. Mikäli käytät Chrome tai Edge-selainta muista unmute!</p> 
    <iframe width="420" height="250" src="https://www.youtube.com/embed/{youtube}?autoplay=1" allow="autoplay"></iframe><br> 
    <hr> 
    <p style="font-size: 0.80em;">Kortin toimittanut Kekkoslovakian Joulukortti Ky</p> 
    </center> 
    </body> 
    </html> """

    return sivu


def tietokantayhteys():
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
    
    # otetaan yhteys tietokantaan näitä käyttäen
    try:
        con = psycopg2.connect(database=f"{dbname}", user=f"{user}", password=f"{password}", host=f"{host}")
        return con
        
    except (Exception, psycopg2.DatabaseError) as err:
        logging.error(f'Frontin käyttäjä epäonnistui kortin lähettämisessä tilausjonoon, sillä ohjelmassa tapahtui virhe')
        logging.error(err)
        return "Something went wrong."
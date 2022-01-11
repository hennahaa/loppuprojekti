from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
from secretsconfig import access_secret_version
from uploadblob import uploadaa_template, uploadaa_postikortti_jpg, uploadaa_postikortti_html
from fileparser import csvparser, xlsparser
from downloadblob import download_blob
from google.cloud.storage import Blob
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import random
import string
import psycopg2
import logging
import os

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'csv', 'xlsx'}
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO) # loggaa kaikki infotasosta ylöspäin olevat viestit

# flask appin configuraatioita
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['SECRET_KEY'] = access_secret_version("final-project-2-337107", "flask-app-secret", "latest")

# ei haittaa jos templaten kuva.jpg extension on JPG/JPEG jpg/jpeg pienellä tai isolla
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# hakee yhteyden databaseen
def db_connection():
    try:
        conn = psycopg2.connect(
        host=access_secret_version("final-project-2-337107", "kekkoslovakia-db-ip", "latest"),
        database=access_secret_version("final-project-2-337107", "kekkoslovakia-db-name", "latest"),
        user=access_secret_version("final-project-2-337107", "kekkoslovakia-db-user", "latest"),
        password=access_secret_version("final-project-2-337107", "kekkoslovakia-db-srv-pw", "latest"))
        return conn
    except (Exception, psycopg2.DatabaseError) as err:
        logging.error(err)
        conn = None

# hakee templatet
def get_templates():
    conn = db_connection()
    cur = conn.cursor()
    SQL = "SELECT * FROM templates;"
    cur.execute(SQL)
    return cur.fetchall()

# vie templatet index.html:ään
@app.route('/')
def index():
    templates = get_templates()
    return render_template('index.html', templates=templates)

# templaten lisäys
@app.route('/add-templ', methods = ['POST', 'GET'])
def add_templ():
    # hakee index.html:stä formitiedot
    tiedostoformista = request.files['jpgfromuser']
    nimi = request.form['template_nimi']
    kuvaus = request.form['template_kuvaus']

    # jos frontissa ei annettu jotain tietoja tiedostoa heittää feilisivun (kivikautinen toteutus)
    if tiedostoformista.filename == "":
        return render_template('template-tiedosto-fail.html')

    if nimi == "":
        return render_template('template-nimi-fail.html')

    # poistaa urlia varten välit ja korvaa ne viivalla, kaikki lowercase
    destinationnimi = nimi.replace(' ','-')
    destinationnimi = destinationnimi.lower()
    destinationnimi = secure_filename(destinationnimi)

    tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-bucket/templates/{destinationnimi}"

    # secure filename tekee tiedostonnimestä vielä enemmän nätin käsittelyä varten, esim. ääkköset poistuu
    if tiedostoformista and allowed_file(tiedostoformista.filename):
        tiedostoformista.save(secure_filename(tiedostoformista.filename))
        uploadaa_template("kekkoslovakia-bucket",tiedostoformista.filename,destinationnimi)

    # yhteys db:hen
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO templates (name, description, image)
        VALUES (%s,%s,%s);
        """,
        (nimi, kuvaus, tiedostourl_bucketissa))
    conn.commit()

    # deletoi lokaalin tiedoston appin polusta samantien
    os.remove(tiedostoformista.filename)

    logging.info(f'Frontin käyttäjä lisännyt templaten "{nimi}"')
    return render_template('add-templ-onnistui.html')

# poistaa templaten
@app.route('/del-templ', methods = ['POST', 'GET'])
def del_templ():
    valinta = request.form.get('poistovalinta')
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM templates
        WHERE name=%s;
        """,
        (valinta,))
    conn.commit()
    logging.info(f'Frontin käyttäjä poistanut templaten "{valinta}"')
    return render_template('del-templ-onnistui.html')

# random string generator
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

# ensimmäinen lähetys ennen vahvistussivua ja varsinaista lähettämistä
@app.route('/send-initial', methods = ['POST', 'GET'])
def send_initial():
    tiedot = []
    # hakee index.html:stä formitiedot, lisää listaan edelleenpassausta varten
    syot_template_nimi = request.form['syot_template_nimi']
    tiedot.append(syot_template_nimi)
    syot_saajan_nimi = request.form['syot_saajan_nimi']
    tiedot.append(syot_saajan_nimi)
    syot_saajan_sposti = request.form['syot_saajan_sposti']
    tiedot.append(syot_saajan_sposti)
    syot_lahet_nimi = request.form['syot_lahet_nimi']
    tiedot.append(syot_lahet_nimi)
    syot_lahet_viesti = request.form['syot_lahet_viesti']
    tiedot.append(syot_lahet_viesti)
    syot_yt_link = request.form['syot_yt_link']
    tiedot.append(syot_yt_link)

    if syot_yt_link[:32] != "https://www.youtube.com/watch?v=":
        return render_template('init-yt-fail.html')

    # parsee templaten nimen ymmärrettäväksi kuvanluojalle
    syot_template_nimi_parsettu = syot_template_nimi.replace(' ','-')
    syot_template_nimi_parsettu = syot_template_nimi_parsettu.lower()
    syot_template_nimi_parsettu = secure_filename(syot_template_nimi_parsettu)

    # lataa template lokaalisti käsiteltäväksi
    download_blob("kekkoslovakia-bucket",syot_template_nimi_parsettu,syot_template_nimi_parsettu)

    # luo kuvan lokaalisti
    tiedostonnimi = f"{syot_template_nimi_parsettu}"
    img = Image.open(tiedostonnimi)
    draw = ImageDraw.Draw(img)
    # asettaa fontit
    font = ImageFont.truetype("Roboto-Regular.ttf", 42)
    font2 = ImageFont.truetype("Roboto-Regular.ttf", 32)
    # piirtää tekstin
    draw.text((32, 110),f"Hei {syot_saajan_nimi},",(0,0,0),font=font2)
    draw.text((53, 228),f"{syot_lahet_viesti}",(0,0,0),font=font)
    draw.text((420, 410),f"{syot_lahet_nimi}",(0,0,0),font=font)
    randomstringi = get_random_string(8)
    randomtiedostonnimi = randomstringi + ".jpg"
    img.save(f"static/temp/{randomtiedostonnimi}")
    tiedot.append(f"temp/{randomtiedostonnimi}")
    os.remove(syot_template_nimi_parsettu)
    return render_template('confirm.html', tiedot=tiedot)

# varsinainen lähettäminen
@app.route('/send-final', methods = ['POST', 'GET'])
def send_final():
    # hakee confirm sivun final formista tiedot
    final_template_nimi = request.form['final_template_nimi']
    final_saajan_nimi = request.form['final_saajan_nimi']
    final_saajan_sposti = request.form['final_saajan_sposti']
    final_lahet_nimi = request.form['final_lahet_nimi']
    final_lahet_viesti = request.form['final_lahet_viesti']
    final_kuva = request.form['final_kuva']
    final_youtube = request.form['final_youtube']

    # parsetaan youtube-linkki samantien
    final_youtube = final_youtube[-11:]

    buckettiin_tiedostonnimi = final_kuva[5:]
    pathi_mista_haetaan = f"static/temp/{buckettiin_tiedostonnimi}"

    # jpg-postikortin lähetys bucketiin
    uploadaa_postikortti_jpg(f"kekkoslovakia-cards", pathi_mista_haetaan, buckettiin_tiedostonnimi)

    # tyhjentää temp-kansion sisällön, koska siellä ei tarvitse olla yhtään jpg:tä tämän jälkeen
    # esim. jos tekee kuvan mutta ei lähetä sitä se jää kummittelemaan temp-kansioon
    # logiikka: on kuitenkin syytä olettaa, että joku jossain vaiheessa onnistuu kortin teossa/pääsee tänne saakka :)
    dir = f"static/temp"
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))

    # luo html
    randomstringi = get_random_string(8)
    randomtiedostonnimi = randomstringi + ".html"
    f = open(randomtiedostonnimi, 'w', encoding = "utf-8")

    kortti_jpg_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/jpg/{buckettiin_tiedostonnimi}"
    kortti_html_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/html/{randomtiedostonnimi}"

    message = f"""<!DOCTYPE html>
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
    <img class="img-fluid" src="{kortti_jpg_tiedostourl_bucketissa}"><br>
    <br><p>Lähettäjä halusi lisätä kortin yhteydeen oman audioraidan. Mikäli käytät Chrome tai Edge-selainta muista unmute!</p>
    <iframe width="420" height="250" src="https://www.youtube.com/embed/{final_youtube}?autoplay=1" allow="autoplay"></iframe><br>
    <hr>
    <p style="font-size: 0.80em;">Kortin toimittanut Kekkoslovakian Joulukortti Ky</p>
    </center>
    </body>
    </html>"""

    f.write(message)
    f.close()

    uploadaa_postikortti_html("kekkoslovakia-cards", randomtiedostonnimi, randomtiedostonnimi)
    
    # viestin pituuden haku data-analyysiä varten
    viestinpituus = len(final_lahet_viesti)
    # tokenin generointi linkkitablea varten
    tokeni = get_random_string(15)

    # juttujen lähetys tilausjonoon
    try:
        conn = db_connection()
        cur = conn.cursor()
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
        conn.commit()
        logging.info(f'Frontin käyttäjä on onnistuneesti lähettänyt kortin tilausjonoon. Saaja: {final_saajan_sposti}, JPG url: {kortti_jpg_tiedostourl_bucketissa}, HTML url: {kortti_html_tiedostourl_bucketissa}')
        os.remove(randomtiedostonnimi) # poistaa lokaalin html:n
        return render_template('onnistui.html')
    except (Exception, psycopg2.DatabaseError) as err:
        logging.error(f'Frontin käyttäjä epäonnistui kortin lähettämisessä tilausjonoon, sillä ohjelmassa tapahtui virhe')
        logging.error(err)
        # tähän voisi oikeassa tilanteessa lisätä jonkun emaililähetysjutun/alertin, koska kyseessä on sen verran perustavanlaatuinen virhe
        os.remove(randomtiedostonnimi) # poistaa lokaalin html:n
        return render_template('epaonnistui.html')

# initial massa lähettäminen
@app.route('/send-massa', methods = ['POST', 'GET'])
def send_massa():
    tiedot = []
    # hakee index.html:stä formitiedot, lisää listaan edelleenpassausta varten
    massa_template_nimi = request.form['massa_template_nimi']
    tiedot.append(massa_template_nimi) # tiedot 0
    massa_lahet_nimi = request.form['massa_lahet_nimi']
    tiedot.append(massa_lahet_nimi) # tiedot 1
    massa_lahet_viesti = request.form['massa_lahet_viesti']
    tiedot.append(massa_lahet_viesti) # tiedot 2
    massa_yt_link = request.form['massa_yt_link']
    tiedot.append(massa_yt_link) # tiedot 3

    excelformista = request.files['excelfromuser']
    if excelformista.filename[-5:] == ".xlsx":
        postituslista = xlsparser(excelformista)
    elif excelformista.filename[-4:] == ".csv":
        excelformista.save(secure_filename(excelformista.filename))
        postituslista = csvparser(excelformista.filename)
    else:
        return render_template('excel-file-fail.html')

    if massa_yt_link[:32] != "https://www.youtube.com/watch?v=":
        return render_template('init-yt-fail.html')

    # parsee templaten nimen ymmärrettäväksi kuvanluojalle
    massa_template_nimi_parsettu = massa_template_nimi.replace(' ','-')
    massa_template_nimi_parsettu = massa_template_nimi_parsettu.lower()
    massa_template_nimi_parsettu = secure_filename(massa_template_nimi_parsettu)

    # lataa template lokaalisti käsiteltäväksi
    download_blob("kekkoslovakia-bucket",massa_template_nimi_parsettu,massa_template_nimi_parsettu)

    # luo kuvan lokaalisti
    tiedostonnimi = f"{massa_template_nimi_parsettu}"
    img = Image.open(tiedostonnimi)
    draw = ImageDraw.Draw(img)
    # asettaa fontit
    font = ImageFont.truetype("Roboto-Regular.ttf", 42)
    font2 = ImageFont.truetype("Roboto-Regular.ttf", 32)
    # piirtää tekstin
    draw.text((32, 110),f"Hei,",(0,0,0),font=font2)
    draw.text((53, 228),f"{massa_lahet_viesti}",(0,0,0),font=font)
    draw.text((420, 410),f"{massa_lahet_nimi}",(0,0,0),font=font)
    randomstringi = get_random_string(8)
    randomtiedostonnimi = randomstringi + ".jpg"
    img.save(f"static/temp/{randomtiedostonnimi}")
    tiedot.append(f"temp/{randomtiedostonnimi}") # tiedot 4
    os.remove(massa_template_nimi_parsettu)
    if excelformista.filename[-4:] == ".csv":
        os.remove(excelformista.filename)
    print(postituslista)
    return render_template('confirm-massa.html', tiedot=tiedot, postituslista=postituslista)

# varsinainen massalähettäminen
@app.route('/send-massa-final', methods = ['POST', 'GET'])
def send_massa_final():
    # hakee confirm sivun final formista tiedot
    final_massa_template_nimi = request.form['final_massa_template_nimi']
    print(final_massa_template_nimi)
    final_massa_saajien_nimet_spostit = request.form['final_massa_saajien_nimet_spostit']
    print(final_massa_saajien_nimet_spostit)
    final_massa_lahet_nimi = request.form['final_massa_lahet_nimi']
    print(final_massa_lahet_nimi)
    final_massa_lahet_viesti = request.form['final_massa_lahet_viesti']
    print(final_massa_lahet_viesti)
    final_massa_kuva = request.form['final_massa_kuva']
    print(final_massa_kuva)
    final_massa_yt_link = request.form['final_massa_yt_link']
    print(final_massa_yt_link)

    # parsetaan youtube-linkki samantien
    final_youtube = final_massa_yt_link[-11:]

    buckettiin_tiedostonnimi = final_massa_kuva[5:]
    pathi_mista_haetaan = f"static/temp/{buckettiin_tiedostonnimi}"

    # jpg-postikortin lähetys bucketiin
    uploadaa_postikortti_jpg(f"kekkoslovakia-cards", pathi_mista_haetaan, buckettiin_tiedostonnimi)

    # tyhjentää temp-kansion sisällön, koska siellä ei tarvitse olla yhtään jpg:tä tämän jälkeen
    # esim. jos tekee kuvan mutta ei lähetä sitä se jää kummittelemaan temp-kansioon
    # logiikka: on kuitenkin syytä olettaa, että joku jossain vaiheessa onnistuu kortin teossa/pääsee tänne saakka :)
    dir = f"static/temp"
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))

    # luo html
    randomstringi = get_random_string(8)
    randomtiedostonnimi = randomstringi + ".html"
    f = open(randomtiedostonnimi, 'w', encoding = "utf-8")

    kortti_jpg_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/jpg/{buckettiin_tiedostonnimi}"
    kortti_html_tiedostourl_bucketissa = f"https://storage.googleapis.com/kekkoslovakia-cards/html/{randomtiedostonnimi}"

    message = f"""<!DOCTYPE html>
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
    <img class="img-fluid" src="{kortti_jpg_tiedostourl_bucketissa}"><br>
    <br><p>Lähettäjä halusi lisätä kortin yhteydeen oman audioraidan. Mikäli käytät Chrome tai Edge-selainta muista unmute!</p>
    <iframe width="420" height="250" src="https://www.youtube.com/embed/{final_youtube}?autoplay=1" allow="autoplay"></iframe><br>
    <hr>
    <p style="font-size: 0.80em;">Kortin toimittanut Kekkoslovakian Joulukortti Ky</p>
    </center>
    </body>
    </html>"""

    f.write(message)
    f.close()

    uploadaa_postikortti_html("kekkoslovakia-cards", randomtiedostonnimi, randomtiedostonnimi)
    
    # final massa saajien nimet pitää käsitellä uudestaan koska frontissa se kääntää listan stringimuotoon :(
    uus_final_mass = final_massa_saajien_nimet_spostit.replace("'", "")
    uus_final_mass2 = uus_final_mass.replace("]", "")
    uus_final_mass3 = uus_final_mass2.replace("[", "")
    uus_final_mass4 = uus_final_mass3.replace(" ", "")

    data = uus_final_mass4.split(',')
    uus = list(zip(data[::2],data[1::2]))
    
    # viestin pituuden haku data-analyysiä varten
    viestinpituus = len(final_massa_lahet_viesti)
    try:
        conn = db_connection()
        cur = conn.cursor()
        for item in uus:
            nimi = item[0]
            sposti = item[1]
            tokeni = get_random_string(15)
            cur.execute("""
                INSERT INTO tilausjono (template_nimi, saajan_nimi, saajan_sposti, lahet_nimi, lahet_viesti, viest_pituus, final_kuva, final_youtube, html_sivu)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
                """,
                (final_massa_template_nimi,nimi,sposti,final_massa_lahet_nimi,final_massa_lahet_viesti,viestinpituus,final_massa_kuva,final_youtube,randomtiedostonnimi))
            cur.execute("""
                INSERT INTO tokenilinkit (tokeni, jpg_bucketissa, html_bucketissa, html_tiedosto)
                VALUES (%s,%s,%s,%s);
                """,
                (tokeni,kortti_jpg_tiedostourl_bucketissa,kortti_html_tiedostourl_bucketissa,randomtiedostonnimi))
        conn.commit()
        logging.info(f'Frontin käyttäjä on onnistuneesti massalähettänyt kortteja tilausjonoon. JPG url: {kortti_jpg_tiedostourl_bucketissa}, HTML url: {kortti_html_tiedostourl_bucketissa}')
        os.remove(randomtiedostonnimi) # poistaa lokaalin html:n
        return render_template('onnistui.html')
    except (Exception, psycopg2.DatabaseError) as err:
        logging.error(f'Frontin käyttäjä epäonnistui kortin lähettämisessä tilausjonoon, sillä ohjelmassa tapahtui virhe')
        logging.error(err)
        # tähän voisi oikeassa tilanteessa lisätä jonkun emaililähetysjutun/alertin, koska kyseessä on sen verran perustavanlaatuinen virhe
        os.remove(randomtiedostonnimi) # poistaa lokaalin html:n
        return render_template('epaonnistui.html')

# kortin lähettämisen onnistumisviesti
@app.route('/onnistui')
def success():
    return render_template('onnistui.html')

# 404-sivu
@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
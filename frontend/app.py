from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
from secretsconfig import access_secret_version
from uploadblob import upload_blob
from google.cloud.storage import Blob
import psycopg2
import logging
import os

ALLOWED_EXTENSIONS = {'jpg', 'jpeg'} # jpg tai jpeg sallittu tässä appissä, ei esim. bash scriptejä :)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO) # loggaa kaikki infotasosta ylöspäin olevat viestit

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
#app.config['SECRET_KEY'] = None

# ei haittaa jos templaten kuva.jpg extension on JPG tai jpg pienellä tai isolla
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# if __name__ == '__main__':
#     app.run(host='0.0.0.0')

def db_connection():
    try:
        conn = psycopg2.connect(
        host=None,
        database=None,
        user=None,
        password=None)
        return conn
    except (Exception, psycopg2.DatabaseError) as err:
        logging.error(err)
        conn = None

def get_templates():
    conn = db_connection()
    cur = conn.cursor()
    SQL = "SELECT * FROM templates;"
    cur.execute(SQL)
    return cur.fetchall()

@app.route('/')
def index():
    templates = get_templates()
    return render_template('index.html', templates=templates)

@app.route('/add-templ', methods = ['POST', 'GET'])
def add_templ():
    # hakee index.html:stä formitiedot
    tiedostoformista = request.files['jpgfromuser']
    nimi = request.form['template_nimi']
    print(nimi)
    kuvaus = request.form['template_kuvaus']

    # jos frontissa ei annettu jotain tietoja tiedostoa
    if tiedostoformista.filename == "":
        return render_template('template-tiedosto-fail.html')

    if nimi == "":
        return render_template('template-nimi-fail.html')

    # poistaa urlista välit ja korvaa ne viivalla, kaikki lowercase
    destinationnimi = nimi.replace(' ','-')
    destinationnimi = destinationnimi.lower()

    tiedostourl_bucketissa = f"None"

    if tiedostoformista and allowed_file(tiedostoformista.filename):
        tiedostoformista.save(secure_filename(tiedostoformista.filename))
        upload_blob("None",tiedostoformista.filename,destinationnimi)

    conn = db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO templates (name, description, image)
        VALUES (%s,%s,%s);
        """,
        (nimi, kuvaus, tiedostourl_bucketissa))
    conn.commit()

    # deletoi lokaalin tiedoston samantien
    os.remove(tiedostoformista.filename)

    logging.info(f'Käyttäjä lisännyt templaten {nimi}')
    return render_template('add-templ-onnistui.html')

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
    return render_template('del-templ-onnistui.html')

@app.route('/epaonnistui')
def fail():
    return render_template('epaonnistui.html')

@app.route('/onnistui')
def success():
    return render_template('onnistui.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404
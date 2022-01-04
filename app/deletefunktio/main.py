# TO DO: tietokannan speksit haettava salaisuuksista kovakoodauksen sijasta

import psycopg2
#from google.cloud import secretmanager
import json
    
def poistatoken(request):
    """Poistaa e-korttitokenin tietokannasta, trigger JavaScriptistä API Gatewayhin frontista"""
    con = None
    try:
        con = psycopg2.connect(database="", user="", password="", host="")
        cursor = con.cursor()

        request_json = request.get_json(silent=True)
        token = request_json.get("token")
        
        SQL = '''UPDATE linkit SET token = NULL WHERE token = %s;'''
        cursor.execute(SQL, (token,))
        con.commit()
                
        cursor.close()
        return 'Token deleted.'

    except (Exception,psycopg2.DatabaseError) as error:
        print(error)
        return 'Something went wrong'
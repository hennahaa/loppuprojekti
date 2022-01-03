#TODO määritä connection (rivi 10), kun tietokannan speksit tiedossa: haetaanko secret managerista vai esim. ympäristömuuttujista?
#TODO tablen nimi SQL:än (rivi 15), kun tietokannan speksit tiedossa

import psycopg2

def poistatoken(event, token):
    """Poistaa e-korttitokenin tietokannasta, trigger JavaScriptistä API Gatewayhin frontista"""
    con = None
    try:
        con = psycopg2.connect('dbname= user= password= host=')
    except (Exception,psycopg2.DatabaseError) as error:
        print(error, "Could not connect to database.")    
        
    cursor = con.cursor()
    SQL = '''DELETE FROM #tablename WHERE token = %s;'''
    cursor.execute(SQL, token)
    con.commit()
    print(f"Poistettu token {token}.")
    cursor.close()
    
    if con is not None:
            con.close()
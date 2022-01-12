import csv
import pandas as pd

# csvparser.py ottaa vastaan csv-tiedoston, palauttaa listan jossa nimi:sähköposti
def csvparser(tiedostonnimi):
    with open(tiedostonnimi, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
    return data

# xlsparser.py ottaa vastaan xlsx-tiedoston, muuttaa sen csv:ksi ja palauttaa listan jossa nimi:sähköposti
def xlsparser(tiedostonnimi):
    read_file = pd.read_excel (tiedostonnimi)
    read_file.to_csv ("temp.csv", 
                    index = None,
                    header=True)

    with open('temp.csv', newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
    return data
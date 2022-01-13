# Käyttö

## Yhteys tietokantaan

Yhteys kantoihin otetaan virtuaalikoneiden kautta. `kekkoslovakia-henkilosto` ja `kekkoslovakia-reskontra`-instansseilla ei ole julkisia ip-osoitteita, ja niihin ei voi sellaisenaan ottaa ssh- tai etätyöpöytä-yhteyttä. 

`kekkoslovakia-bastion`-instanssiin voi ottaa yhteyden tällä hetkellä mistä tahansa ip-osoitteesta. Bastionin firewall-säännön voi myöhemmin määrittää tarkemmin siten, että siihen voidaan ottaa yhteys vain tietyistä kekkoslovakian omista ulkoisista ip-osoitteista. 

`kekkoslovakia-bastion`-instanssista voi ottaa yhteyden verkon sisäisiin virtuaalikoneisiin, joista puolestaan saa yhteyden tietokantaan. 

`kekkoslovakia-bastion` -> `kekkoslovakia-henkilöstö`:

    gcloud compute ssh kekkoslovakia-henkilosto --internal-ip

`kekkoslovakia-bastion` -> `kekkoslovakia-reskontra`:

vaatii salasanan generoinnin konsolista googlen dokumentaation mukaisesti: https://cloud.google.com/compute/docs/instances/windows/generating-credentials

`kekkoslovakia-henkilöstö` -> `kekkoslovakia-db-backend-prod`

    psql -h <INTERNAL-IP> -p 5432 -d kekkoslovakia-db-backend-prod -U <DB-USER>

(komento tässä muodossaan kysyy tietokannan käyttäjähn salasanaa)
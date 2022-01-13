![Korttigeneraattorisivun valikot](https://github.com/hennahaa/loppuprojekti/blob/tiina-kertakayttolinkki/docs/images/korttigeneraattori.png)

## Yleistä korttigeneraattorista
Korttigeneraattori on Pythonilla kirjoitettu Flask app, joka on dockeroitu (koko 257 kilotavua unzipattuna versiossa 0.3) ja suunniteltu toimimaan Cloud Runissa (mutta sovellettavissa myös muihin ympäristöihin). Web Server Gateway Interfacen virkaa hoitaa Gunicorn, jonka eteen on mahdollista production-versioon lisätä Nginx reverse proxyksi.

## Korttigeneraattorin käyttö

##### Kortin tekeminen
1. Uuden kortin luonti
2. Tarkastele eri templateja alhaalta. Templateja lisätään ja poistetaan Admin-osiosta.
3. Valitse lomakkeesta (sivun alalaidassa) alasvetovalikosta template, syötä saajan nimi, saajan sähköpostiosoite, lähettäjän nimi, ja tervehdysviesti. Kenttien maksimipituus on 12 merkkiä, pl. sähköposti-kenttä, jonka maksimipituus on 64 merkkiä.
4. Uutta versiossa 0.2! Asiakkaan antama YouTube-linkki lisätään postikorttiin. Annathan sen muodossa https://www.youtube.com/watch?v=tjt-AeJkzf0 .
5. Paina sinistä "Lähetä"-nappulaa. Tarkista esikatselusivulta, että tiedot on syötetty oikein, ja viimeistele lähetys klikkaamalla sinistä "Lähetä"-nappulaa.

Postikortin lähetyksen hoitaa ViestiVompatit Oy.


##### Massapostitus-välilehti
Massapostitus ottaa vastaan joko yhden .xlsx (Excel) tai .csv-tiedoston. 

Tiedostossa tiedot pitää olla vierekkäisissä sarakkeissa, sarake A: etunimi, sarake B: sähköposti. Tiedostossa ei saa olla sarakkeita kuvaavia otsikoita, vaan pelkkää dataa. Eli solu A1 on jo nimi ja solu B1 on jo sähköpostiosoite.
CSV-tiedostossa yhden rivin pitää olla muodossa etunimi,sähköposti@example.com . 

Muilta ominaisuuksilta osin massapostitus toimii kuten yhden kortin lähettäminen tilausjonoon.

1. Valitse "Choose file"-napista avautuvasta valikosta massapostitustiedostosi.
2. Täytä muut kentät samoin kuin yllä olevassa ohjeessa yksittäisen kortin tekemiseen.


##### Admin-välilehti
**Korttipohjien lisääminen**
1. Valitse luomasi kuvatiedosto (750 x 525 pikseliä) Choose file -napista avautuvasta valikosta.
2. Nimeä template (korttipohja), tahtoessasi kirjoita sille kuvaus.
3. Lisää template (korttipohja) korttigeneraattoriin sinisestä "Lisää"-napista.

**Korttipohjien poistaminen**
1. Valitse alasvetovalikosta korttipohja, jonka tahdot poistaa.
2. Poista korttipohja sinisestä "Poista"-napista. HUOM! Poistamista ei voi perua.


![Webbisovelluskokonaisarkkitehtuurikaavio](https://github.com/hennahaa/loppuprojekti/blob/tiina-kertakayttolinkki/docs/images/app-kaavio.png)

## Webbisovelluksen konepellin alla

Korttigeneraattorista tiedot siirtyvät json-muodossa **API Gatewayn** (ja **Google Cloud Functions** -toimintojen käsitteleminä) tietokantoihin, josta ne on mahdollista myös palauttaa.

API Gatewayn konfigurointi on suoritettu [Swagger 2.0](https://swagger.io/specification/v2/) käyttäen. Funktioiden toiminnallisuus on selvitetty kunkin funktion koodissa.

Koko kortinjulkaisualustasovellus on provisoitavissa Terraformilla.
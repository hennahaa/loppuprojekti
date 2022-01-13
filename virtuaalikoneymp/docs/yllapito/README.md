# Ylläpito-ohje

## Virtuaalikoneet

### Snapshotit
Virtuaalikoneista otetaan snapshottina backup kerran vuorokaudessa. Snapshotin otto tapahtuu noin kello 6-7 välillä UTC +0 aikavyöhykkeellä.

Koneet, joista snapshotit otetaan, ovat
* kekkoslovakia-bastion
* kekkoslovakia-henkilosto
* kekkoslovakia-reskontra


![instanssit](https://github.com/hennahaa/loppuprojekti/blob/henna-dev/virtuaalikoneymp/docs/images/instanssit.PNG?raw=true)

### Reskontrakone
Kekkoslovakia-reskonra pitää sisällään Passeli Pro-ohjelmiston ja binääritietokannan. Itse koneesta voidaan ottaa backup snapshottina, mutta tietokannasta täytyy ottaa backup Passelin omien ohjeiden mukaan.

### Koneiden palautus
Snapshotit löytyvät konsolista Compute Engine -> Snapshots

![snapshotit](https://github.com/hennahaa/loppuprojekti/blob/henna-dev/virtuaalikoneymp/docs/images/backup.PNG?raw=true)

### Cloud SQL
Tietokantainstanssi käyttää Point in Time recoverya. Tietokannan palautustoiminnon löytää navigoimalla SQL -> Backups, tällä sivulla on RESTORE-painike, jolla kannan voi palauttaa tarvittaessa.

![restore](https://github.com/hennahaa/loppuprojekti/blob/henna-dev/virtuaalikoneymp/docs/images/restore.PNG?raw=true)
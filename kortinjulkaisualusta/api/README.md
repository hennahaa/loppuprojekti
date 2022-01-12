# Korttijulkaisualusta
## Kansiorakenne:

    NYT:
    -------
    ├──app/
    │   ├──api-gateway/
    │   ├──functions/
    │   │   ├──haekaikki/
    │   │   ├──haekortti/
    │   │   ├──lisaatoken/
    │   │   └──poistatoken/
    │   └──terraform/
    ├──backend/
    │  └──terraform/
    ├──docs/
    └──frontend-cloudrun/
        ├──static/photos/
        └──templates/

    ESIM:
    ----
    ├──kortinjulkaisualusta/
    │   ├──api/
    │   │   ├──api-gateway/
    │   │   ├──functions/
    │   │   │   ├──haekaikki/
    │   │   │   ├──haekortti/
    │   │   │   ├──lisaakortti/
    │   │   │   ├──lisaatoken/
    │   │   │   └──poistatoken/
    │   ├──docs/
    │   ├──frontend-cloudrun/
    │   │    ├──static/photos/
    │   │    └──templates/
    │   └──terraform/
    └──virtuaalikoneymp/
        ├──terraform/
        └──docs/
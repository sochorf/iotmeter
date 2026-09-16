# Historie vydání

## 1.0.3

- Stavový kód EVSE 3 se zobrazuje jako `charging`; ověřeno uživatelem při skutečném nabíjení.
- Připojení vozu zůstává `on` také během nabíjení (kód 3).
- Každá stanice získává vlastní binární senzor `iotmeter_evseN_charging`.
- Neznámé kódy a chyba zdroje znamenají nedostupnou indikaci, nikoli vypnuté nabíjení.
- Existující názvy, unique_id, interval a počet API dotazů jsou zachovány.

Po aktualizaci restartujte Home Assistant. Existující integraci nemažte.
Ověřena syntaxe Pythonu a izolovaná logika kódů 1/2/3, neznámého kódu a chybějících dat. Běh v HA bude ověřen po nasazení.

## 1.0.2

- Přidána metadata pro instalaci a aktualizace přes HACS.
- Přidány místní obrázky do složky `brand` pro Home Assistant 2026.3 a novější.
- README popisuje zařízení, podporované funkce, instalaci, nastavení a diagnostiku.
- Z manifestu odstraněny nepodporované položky `icon` a `logo` a neověřené hodnocení `quality_scale`.

Funkční Python kód se oproti importované verzi 1.0.1 nezměnil. Toto vydání nepotvrzuje opravu zobrazování obrázků v konkrétní instalaci HA nebo HACS.

### Instalace

Po aktualizaci přes HACS restartujte Home Assistant. Existující integraci v Zařízení a služby nemažte ani znovu nepřidávejte.

### Ověření

Ověřena syntaxe Pythonu, validita souborů JSON a shoda funkčního kódu s výchozím importem. Běhové testování v HA nebylo součástí přípravy vydání.

## 1.0.1

Výchozí import integrace z dodané zálohy. Starší historie změn není k dispozici.

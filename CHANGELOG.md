# Historie vydání

## 1.0.4 – oddělené intervaly a session pro každou dávku

- `/updateData`: cílový interval 5 s; `/updateEvse`: 10 s; `/updateSetting`: 60 s.
- Každá čtecí dávka vytváří vlastní HTTP session a po dokončení ji uzavře, obdobně jako autorova integrace. TCP spojení se nepřenášejí mezi dávkami; uvnitř dávky je možné opětovné použití.
- Požadavky zůstávají postupné, nikoli souběžné. Data se čtou na konci dávky, aby byla při zveřejnění co nejčerstvější.
- Timeout zůstává 10 s na požadavek. Bez okamžitých retry a bez dohánění zmeškaných cyklů. Skutečné intervaly mohou být delší kvůli odpovědím a plánování HA.
- Po úspěšném zápisu z HA se vyžádá přednostní načtení settings. Externí změny nastavení se jinak mohou projevit až po minutě či déle při výpadku.
- Přeskočené endpointy si zachovají stav dostupnosti a původní `last_success`. Neúspěšné čtení nadále znamená unavailable; toto vydání chyby nezakrývá tolerancí cache.
- Debug log doplněn o dobu každého požadavku; komunikační chyba obsahuje typ výjimky.
- Entity, unique_id, kódy EVSE a výpočty energie se nemění. Ruční zápisy nadále používají session HA; změna životnosti session se týká periodického čtení.

### Aktualizace a ověření

Aktualizujte integraci přes HACS a restartujte HA. Existující integraci nemažte.
Sledujte skutečné intervaly `last_success` a výpadky dostupnosti během 24 hodin;
schopnost firmware zvládat keep-alive zatím není prokázaná. Porovnejte s předchozí verzí.

Prošlo 6 izolovaných testů koordinátoru, včetně skutečného lokálního HTTP serveru:
plánování, čerstvé session, sériové požadavky, chyba zdroje, validace ID,
vyžádané settings a uzavření při zrušení. Testy používají minimální mock HA;
nejde o integrační test v běžícím Home Assistantu ani na fyzickém ESP32.

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

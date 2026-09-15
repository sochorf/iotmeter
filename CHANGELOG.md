# Historie vydání

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

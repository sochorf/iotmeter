# IoTMeter pro Home Assistant

Vlastní integrace pro Home Assistant. Výchozí stav pochází z uživatelské zálohy `iotmeter.zip` dodané 15. 9. 2026; manifest uvádí verzi `1.0.1`. Starší historie změn není k dispozici.

## Struktura

`custom_components/iotmeter/` obsahuje přesnou kopii zdrojových souborů ze zálohy. Python cache a metadata macOS jsou vynechány. Součástí nejsou nastavení HA ani provozní data.

## Další změny

1. Začít z aktuální větve `main` a vytvořit pracovní větev.
2. Upravit kód v repozitáři a zkontrolovat `git diff`.
3. Provést vhodné kontroly. Kontrola syntaxe sama neověřuje funkčnost v HA.
4. Uložit logickou změnu samostatným commitem s vysvětlením důvodu.
5. Po kontrole začlenit změnu do `main`.
6. Před nasazením zálohovat dosavadní složku integrace a podle dopadu i HA.
7. Přenést obsah `custom_components/iotmeter/` do `/config/custom_components/iotmeter/` dostupným správcem souborů; nevytvořit další vnořenou složku `iotmeter`.
8. Restartovat Home Assistant a ověřit logy, dostupnost a hodnoty entit.
9. Zapsat datum, nasazený commit (`git rev-parse HEAD`), verzi HA a výsledek do `DEPLOYMENTS.md`.

Při vydání nové verze upravit verzi v manifestu a označit odpovídající commit tagem. První import nezvyšuje verzi a netvrdí, že jde o nově otestované vydání.

## Návrat

Z pracovní kopie předchozího nasazeného commitu obnovit celou složku integrace a restartovat HA. Nepoužívat `git reset --hard` na rozpracovanou pracovní kopii. Pokud změna migrovala uložená data, může být potřeba obnovit i zálohu HA.

## GitHub

Cílový repozitář: https://github.com/sochorf/iotmeter

Remote `origin` je připraven. Před prvním push ověřit obsah vzdáleného repozitáře pomocí `git fetch origin`. Pokud již má historii, nejdřív ji zkontrolovat a propojit s importem; nepoužívat force push. Pro prázdný repozitář použít `git push -u origin main` po přihlášení ke GitHubu.

Repozitář obsahuje metadata pro přidání do HACS. Instalace v konkrétní instanci HA musí být ověřena. Automatické nasazování není nastaveno. Git sleduje tuto pracovní kopii, nikoli soubory měněné přímo v HA.

## Kontroly importu

- Zdrojové soubory odpovídají ZIPu bajt po bajtu.
- Provedena kontrola syntaxe Pythonu a parsování manifestu JSON.
- Orientační kontrola kódu nenašla hesla ani tokeny. Konstanta `VALID_DEVICE_ID` je součást původního kódu.
- Funkčnost v běžícím HA nebyla při importu testována.

## Instalace a aktualizace přes HACS

1. Před prvním převzetím instalace ověřit, že od dodané zálohy nebyly v HA provedeny další úpravy. Pokud ano, nejdřív je importovat do Gitu.
2. Vytvořit aktuální zálohu HA.
3. V HACS otevřít nabídku ⋮ → Vlastní repozitáře, přidat `https://github.com/sochorf/iotmeter` s typem Integrace.
4. Vyhledat IoTMeter a stáhnout požadovanou verzi. Stažení přepíše soubory existující složky integrace.
5. Existující položku IoTMeteru v Nastavení → Zařízení a služby nemazat ani nezakládat znovu.
6. Restartovat HA, ověřit logy a entity a zaznamenat nasazení do DEPLOYMENTS.md.

Dokud neexistuje GitHub Release, HACS používá výchozí větev. Pro řízené aktualizace vydávat GitHub Releases s tagem odpovídajícím verzi manifestu; samotný tag nestačí. Automatické aktualizace neaktivovat, pokud má každému nasazení předcházet kontrola uživatelem. Změny provedené přímo v HA se do GitHubu neodesílají.

Dokumentace: https://www.hacs.xyz/docs/faq/custom_repositories/ a https://www.hacs.xyz/docs/publish/integration/

# IoTMeter pro Home Assistant

Vlastní integrace pro sledování elektrické energie a ovládání nabíjení prostřednictvím zařízení **IoTmeter**. Home Assistant komunikuje se zařízením přímo v místní síti přes HTTP API s odpověďmi JSON; integrace nevyžaduje cloudový účet.

Jde o komunitní projekt, nikoli oficiální integraci výrobce.

## O zařízení

[IoTmeter 65A (WiFi + RS485) od EV Racing](https://www.evracing.cz/iotmeter-65a-wifi-rs485/) je chytrý elektroměr pro instalaci do rozvaděče. Podle výrobce slouží k měření spotřeby a dynamickému řízení nabíjení podle dostupné kapacity sítě, nízkého tarifu HDO a výroby z fotovoltaiky. Nabízí Wi-Fi, HTTP API a rozhraní RS485 master pro stanice EVSE-DIN-RS485. U tohoto modelu výrobce uvádí podporu až tří nabíjecích stanic.

Integrace využívá HTTP API IoTmeteru. Připojení nabíjecích stanic přes RS485 zajišťuje samotný IoTmeter; Home Assistant nepotřebuje vlastní RS485 adaptér.

## Co integrace nabízí

Dostupnost jednotlivých údajů závisí na firmwaru, zapojení a datech vracených zařízením.

| Oblast | Funkce |
|---|---|
| Elektrická síť | Napětí, proud, činný a zdánlivý výkon a účiník jednotlivých fází; součet činného výkonu |
| Energie | Denní a celkové hodnoty odběru a dodávky, údaje po fázích i součty |
| Nabíjení | Údaje EVSE, proudové hodnoty a diagnostika jednotlivých nabíjecích stanic |
| Proudové limity | Nastavení limitu odběru ze sítě, limitu při HDO, podpory ze sítě při nabíjení z FVE a limitů jednotlivých EVSE |
| Režimy | Volba nabíjení ECO / FAST a režimu FVE Off / 1p / 3p |
| Přepínače | Povolení nabíjení, nabíjení podle HDO, vyvažování zátěže a další nastavení vystavená API |
| Diagnostika | Verze firmwaru, chybové údaje a časy posledních úspěšných odpovědí pro nastavení a měření |

Entity lze využít v přehledech a vlastních automatizacích Home Assistantu. Integrace sama neobsahuje plánovač podle cen elektřiny nebo předpovědi výroby FVE.

### Interpretace údajů EVSE

Pro jednotlivé stanice integrace poskytuje stav, původní stavový kód, komunikační chybový údaj a konfigurační a výstupní proud. Proudové hodnoty API nejsou automaticky důkazem skutečného odběru vozidla.

Integrace rozlišuje ověřené stavové kódy `1` (odpojeno), `2` (připojeno) a `3` (nabíjí). Binární senzor `binary_sensor.iotmeter_evseN_connected` je zapnutý pro kódy 2 a 3; nový `binary_sensor.iotmeter_evseN_charging` pouze pro kód 3. Číslo N označuje stanici od 1. Ostatní kódy se zobrazují jako `unmapped` a oba binární senzory jsou nedostupné. Při chybě zdroje jsou rovněž nedostupné, aby nehlásily chybně ukončené nabíjení. Chybové kódy EVSE se předávají bez vlastní interpretace. Indikace nabíjení nepředstavuje měření výkonu a nevyžaduje další API dotazy.

## Požadavky

- Home Assistant s možností instalovat vlastní integrace.
- IoTmeter s dostupným a kompatibilním HTTP API v síti přístupné z HA.
- IP adresa zařízení; doporučujeme rezervaci adresy v DHCP.
- Dostupný TCP port **8000**, který používá současná implementace.
- Pro instalaci přes HACS funkční HACS a přístup ke GitHubu.

Podpora místních ikon ve složce `brand` vyžaduje Home Assistant **2026.3 nebo novější**. To není deklarace minimální otestované verze celé integrace; matice kompatibility HA a firmwaru zatím není k dispozici.

## Instalace přes HACS

Nejdříve musíte mít v Home Assistantu nainstalovaný a nastavený [HACS](https://www.hacs.xyz/docs/use/). IoTMeter přidejte jako vlastní repozitář jedním z následujících způsobů.

### Otevření pomocí tlačítka

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sochorf&repository=iotmeter&category=integration)

1. Klikněte na **Open in HACS**. Pokud vás My Home Assistant požádá o adresu vaší instance HA, zadejte adresu, přes kterou HA běžně otevíráte.
2. Pokračujte tlačítkem **Open link** a v HACS potvrďte přidání repozitáře, pokud se potvrzení zobrazí.
3. Na stránce **IoTMeter** zvolte **Stáhnout**, vyberte nejnovější stabilní vydání a potvrďte stažení.
4. Restartujte Home Assistant a pokračujte částí [Nastavení](#nastavení).

Tlačítko pouze otevře příslušnou stránku; samo nenainstaluje HACS ani integraci. Pokud odkaz nefunguje, použijte ruční postup níže.

### Ruční přidání repozitáře do HACS

1. V Home Assistantu otevřete **HACS**.
2. Vpravo nahoře klikněte na **⋮ → Vlastní repozitáře** (Custom repositories).
3. Do pole **Repozitář** vložte:

   ```text
   https://github.com/sochorf/iotmeter
   ```

4. V poli **Typ** vyberte **Integrace** (Integration) a klikněte na **Přidat**.
5. Zavřete dialog a v seznamu HACS vyhledejte **IoTMeter**. Pokud jej nevidíte, zrušte případné filtry a obnovte stránku.
6. Otevřete IoTMeter, klikněte na **Stáhnout** a potvrďte nejnovější stabilní vydání.
7. Restartujte Home Assistant a pokračujte částí [Nastavení](#nastavení).

### Přechod z ruční instalace

Pokud už používáte `custom_components/iotmeter`, nejdříve zálohujte současné soubory a případné vlastní změny. HACS při stažení nahradí kód ve stejné složce. Existující položku IoTMeteru v **Zařízení a služby** nemažte a nevytvářejte znovu. Po stažení restartujte HA a ověřte původní entity.

## Ruční instalace

1. Z repozitáře zkopírujte složku `custom_components/iotmeter` do složky `custom_components` v konfiguraci HA.
2. Výsledná cesta k manifestu musí být `/config/custom_components/iotmeter/manifest.json` při standardním umístění konfigurace v HA OS.
3. Restartujte Home Assistant a pokračujte nastavením.

## Nastavení

1. Otevřete **Nastavení → Zařízení a služby → Přidat integraci**.
2. Vyhledejte **IoTMeter**.
3. Zadejte IP adresu IoTmeteru, například `192.168.1.50`.
4. Dokončete nastavení a zkontrolujte vytvořené entity.

Zařízení se nejprve ověřuje přes `/updateSetting`. Integrace následně přibližně každých **10 sekund** načítá `/updateSetting`, `/updateEvse` a `/updateData`. Při pomalých odpovědích nebo výpadku může aktualizace trvat déle. Změny ovládacích entit zapisuje zpět do zařízení přes jeho API.

## Aktualizace a návrat ke starší verzi

Aktualizace stahujte přes HACS a poté restartujte HA. Pokud repozitář nabízí GitHub Releases, vyberte požadované vydání; bez vydání HACS používá výchozí větev. Pro ruční kontrolu každé změny ponechte automatické aktualizace vypnuté.

Před aktualizací uchovejte zálohu. Návrat proveďte instalací předchozí dostupné verze nebo obnovením zálohy souborů. Změny provedené přímo v HA se do GitHubu automaticky neukládají a další stažení je může přepsat.

## Řešení problémů

- **Nelze přidat zařízení:** ověřte IP adresu a dostupnost portu 8000 ze sítě HA.
- **Senzory jsou nedostupné:** zkontrolujte spojení a odpovědi API. Dostupnost měřicích a diagnostických senzorů se vyhodnocuje podle příslušného zdroje dat; poslední úspěšná odpověď neprokazuje stáří fyzického měření uvnitř zařízení.
- **Chybí některé entity EVSE:** ověřte nastavený počet stanic a shodu s daty vracenými API.
- **Chybí ikona nebo logo:** ověřte soubory v `custom_components/iotmeter/brand/`, podporovanou verzi HA a restart. HACS může obrázky načítat jiným způsobem než rozhraní HA.
- **Další chyby:** podívejte se do **Nastavení → Systém → Protokoly** a vyhledejte `iotmeter`.

Pro hlášení problémů použijte [GitHub Issues](https://github.com/sochorf/iotmeter/issues). Uveďte verzi HA, integrace, firmwaru zařízení a relevantní výpis chyby bez přihlašovacích nebo jiných citlivých údajů.

## Podpora vývoje

Pokud vám integrace pomáhá, můžete podpořit její další vývoj dobrovolným příspěvkem. Děkuji!

<a href="https://buymeacoffee.com/BIjKcYlRJ"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" width="217" height="60"></a>

## Odkazy

- [IoTmeter 65A – informace výrobce EV Racing](https://www.evracing.cz/iotmeter-65a-wifi-rs485/)
- [Repozitář integrace](https://github.com/sochorf/iotmeter)
- [Přidání vlastního repozitáře do HACS](https://www.hacs.xyz/docs/faq/custom_repositories/)
- [Místní ikony a loga v Home Assistantu](https://developers.home-assistant.io/docs/core/integration/brand_images/)

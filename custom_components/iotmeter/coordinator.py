from __future__ import annotations

import logging
from typing import Any
from datetime import timedelta
from homeassistant.util import dt as dt_util

import asyncio
from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_IP,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    ENDPOINT_SETTINGS,
    ENDPOINT_EVSE,
    ENDPOINT_DATA,
    VALID_DEVICE_ID,
)

_LOGGER = logging.getLogger(__name__)


class IoTMeterCoordinator(DataUpdateCoordinator):
    """Koordinátor pro IoTMeter – tahá settings, evse a data."""

    def __init__(self, hass: HomeAssistant, ip: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="IoTMeter coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._hass = hass
        self._session = async_get_clientsession(hass)

        # ULOŽENÁ IP + PORT + string base_url
        self._ip = ip
        self._port = DEFAULT_PORT
        self.base_url: str = f"http://{ip}:{DEFAULT_PORT}"

        # Výsledek posledního dokončeného pokusu pro každý endpoint zvlášť.
        # False do prvního úspěchu; stará data v cache nejsou důkaz dostupnosti.
        self.source_success = {key: False for key in ("settings", "evse", "data")}
        self.last_success = {key: None for key in self.source_success}

        # poslední „dobrá“ data
        self.data: dict[str, Any] = {
            "settings": None,
            "evse": None,
            "data": None,
        }

    @property
    def ip_address(self) -> str:
        """IP adresa IoTMeteru (pro zápis)."""
        return self._ip

    @property
    def port(self) -> int:
        """Port IoTMeteru (pro zápis)."""
        return self._port

    async def _fetch_json(self, endpoint: str) -> dict[str, Any] | None:
        """Fetch jednoho endpointu z IoTMeteru, vrací JSON nebo None při chybě."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "IoTMeter: HTTP %s při čtení %s",
                        resp.status,
                        url,
                    )
                    return None
                data = await resp.json(content_type=None)
                return data

        except (ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning(
                "IoTMeter: chyba komunikace s %s: %s",
                url,
                err,
            )
            return None
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception(
                "IoTMeter: neočekávaná chyba při čtení %s: %s",
                url,
                err,
            )
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Stejné pořadí, interval a počet dotazů; evidence výsledků po zdrojích.

        Cache uchovává poslední hodnoty, ale sensor.available rozhoduje,
        zda je lze zveřejnit. Časy se mění pouze při validní odpovědi.
        Stav se do entit promítne po dokončení celého cyklu (až tři timeouty).
        Jde o kontrolu odpovědi API, nikoli stáří fyzického měření uvnitř zařízení.
        """
        result = dict(self.data or {})
        for source, endpoint in (
            ("settings", ENDPOINT_SETTINGS),
            ("evse", ENDPOINT_EVSE),
            ("data", ENDPOINT_DATA),
        ):
            payload = await self._fetch_json(endpoint)
            valid = isinstance(payload, dict) and bool(payload)
            if valid and source in ("settings", "data"):
                valid = not VALID_DEVICE_ID or str(payload.get("ID", "")) == VALID_DEVICE_ID
            self.source_success[source] = valid
            if valid:
                result[source] = payload
                self.last_success[source] = dt_util.utcnow()
            else:
                _LOGGER.warning(
                    "IoTMeter: %s bez validní odpovědi; příslušné senzory budou unavailable",
                    source.upper(),
                )
        # Vracíme cache i při výpadku. Dostupnost senzorů je per-source;
        # diagnostické časy proto mohou zůstat viditelné i při úplném výpadku.
        return result

    @staticmethod
    def _evse_integer(value):
        """API číslo nebo celočíselný řetězec; bool ani desetinné hodnoty nebereme."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                pass
        return None

    def evse_count(self):
        """Počet instalovaných wallboxů; nastavení má přednost před odpovědí EVSE.

        Cache nastavení je přípustná: počet instalací není okamžité měření.
        Limit 10 odpovídá současnému ovládání integrace. Žádný další HTTP dotaz.
        """
        data = self.data or {}
        settings = data.get("settings") or {}
        raw = settings.get("in,EVSE-NUMBER", settings.get("EVSE-NUMBER"))
        if raw is None:
            raw = (data.get("evse") or {}).get("NUMBER_OF_EVSE")
        count = self._evse_integer(raw)
        return count if count is not None and 0 <= count <= 10 else None

    def evse_value(self, index, key):
        """Platná položka konkrétního wallboxu, jinak None.

        Po chybě API nesmíme vydávat cache za aktuální stav. Při nesouladu
        počtu nebo délky daného pole je jeho interpretace nejistá.
        Nulový index odpovídá EVSE 1. Kódy chyb zatím neinterpretujeme.
        """
        if not self.last_update_success or not self.source_success.get("evse", False):
            return None
        block = (self.data or {}).get("evse") or {}
        count = self.evse_count()
        reported = self._evse_integer(block.get("NUMBER_OF_EVSE"))
        if count is None or reported != count or not 0 <= index < count:
            return None
        values = block.get(key)
        if not isinstance(values, (list, tuple)) or len(values) != count:
            return None
        return self._evse_integer(values[index])

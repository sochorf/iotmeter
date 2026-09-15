from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import IoTMeterCoordinator

_LOGGER = logging.getLogger(__name__)

# Základní číselná nastavení – vždy přítomná
NUMBER_SETTINGS: list[dict[str, Any]] = [
    {
        "variable": "in,MAX-CURRENT-FROM-GRID-A",
        "entity_id": "number.iotmeter_max_current_from_grid",
        "unique_id": "iotmeter_max_current_from_grid",
        "name": "IoTmeter Max Current from Grid",
        "unit": "A",
        "min": 6,
        "max": 63,
        "step": 1,
    },
    {
        "variable": "in,AC-IN-MAX-CURRENT-FROM-GRID-A",
        "entity_id": "number.iotmeter_max_current_from_grid_hdo",
        "unique_id": "iotmeter_max_current_from_grid_hdo",
        "name": "IoTmeter Max Current from Grid (HDO)",
        "unit": "A",
        "min": 6,
        "max": 63,
        "step": 1,
    },
    {
        "variable": "in,PV-GRID-ASSIST-A",
        "entity_id": "number.iotmeter_pv_grid_assist",
        "unique_id": "iotmeter_pv_grid_assist",
        "name": "IoTmeter PV Grid Assist",
        "unit": "A",
        "min": 0,
        "max": 32,
        "step": 1,
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities,
) -> None:
    """Set up IoTMeter number entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: IoTMeterCoordinator = data["coordinator"]

    entities: list[IoTMeterNumberSetting] = []

    # 1) Globální čísla (jistič, HDO jistič, PV assist)
    for cfg in NUMBER_SETTINGS:
        entities.append(
            IoTMeterNumberSetting(
                coordinator=coordinator,
                config_entry_id=entry.entry_id,
                variable=cfg["variable"],
                entity_id=cfg["entity_id"],
                unique_id=cfg["unique_id"],
                name=cfg["name"],
                unit=cfg["unit"],
                min_value=cfg["min"],
                max_value=cfg["max"],
                step=cfg["step"],
            )
        )

    # 2) Per-EVSE max proudy – jen do počtu in,EVSE-NUMBER
    settings = coordinator.data.get("settings") or {}
    evse_number_raw = settings.get("in,EVSE-NUMBER", "1")
    try:
        evse_count = int(evse_number_raw)
    except (TypeError, ValueError):
        evse_count = 1

    # omezíme na rozumný rozsah 0–10
    if evse_count < 0:
        evse_count = 0
    if evse_count > 10:
        evse_count = 10

    if evse_count == 0:
        _LOGGER.info("IoTMeter: in,EVSE-NUMBER = 0, žádné EVSE number entity nebudou vytvořeny")
    else:
        _LOGGER.info("IoTMeter: vytvářím number entity pro EVSE1..EVSE%d", evse_count)

    for i in range(1, evse_count + 1):
        variable = f"inp,EVSE{i}"
        entities.append(
            IoTMeterNumberSetting(
                coordinator=coordinator,
                config_entry_id=entry.entry_id,
                variable=variable,
                entity_id=f"number.iotmeter_evse{i}_max_current",
                unique_id=f"iotmeter_evse{i}_max_current",
                name=f"IoTmeter EVSE{i} Max Current",
                unit="A",
                min_value=6,   # minimální proud (implicitní 6 A)
                max_value=16,  # typicky 32 A – můžeš si upravit podle instalace
                step=1,
            )
        )

    async_add_entities(entities)


class IoTMeterNumberSetting(CoordinatorEntity, NumberEntity):
    """Number entity napojené na /updateSetting."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: IoTMeterCoordinator,
        config_entry_id: str,
        variable: str,
        entity_id: str,
        unique_id: str,
        name: str,
        unit: str,
        min_value: float,
        max_value: float,
        step: float,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry_id = config_entry_id
        self._variable = variable

        self.entity_id = entity_id
        self._attr_unique_id = unique_id
        self._attr_name = name

        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)},
            name="IoTMeter",
            manufacturer="IoTMeter",
            model="REST-based energy meter",
        )

    @property
    def _settings(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return data.get("settings") or {}

    def _to_float(self, value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @property
    def native_value(self) -> float | None:
        value = self._to_float(self._settings.get(self._variable))
        return value

    async def async_set_native_value(self, value: float) -> None:
        """POST /updateSetting s JSON {'variable': ..., 'value': '<int>'}."""
        hass = self.hass
        ip = self.coordinator.ip_address
        port = self.coordinator.port

        url = f"http://{ip}:{port}/updateSetting"
        session = async_get_clientsession(hass)

        int_value = int(round(value))
        payload = {
            "variable": self._variable,
            "value": str(int_value),
        }

        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                text = await resp.text()
                if resp.status != 200:
                    _LOGGER.error(
                        "IoTMeter: nastavení %s selhalo (HTTP %s): %s",
                        self._variable,
                        resp.status,
                        text,
                    )
                    return
                _LOGGER.debug(
                    "IoTMeter: nastavení %s = %s OK: %s",
                    self._variable,
                    int_value,
                    text,
                )
        except ClientError as err:
            _LOGGER.error(
                "IoTMeter: chyba komunikace při nastavování %s: %s",
                self._variable,
                err,
            )
            return
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception(
                "IoTMeter: neočekávaná chyba při nastavování %s: %s",
                self._variable,
                err,
            )
            return

        await self.coordinator.async_request_refresh()
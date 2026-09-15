from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import IoTMeterCoordinator

_LOGGER = logging.getLogger(__name__)

SELECT_SETTINGS: list[dict[str, Any]] = [
    {
        "variable": "chargeMode",
        "entity_id": "select.iotmeter_charge_mode",
        "unique_id": "iotmeter_charge_mode",
        "name": "IoTmeter Charging Mode",
        "options": [
            {"label": "ECO", "value": "0"},
            {"label": "FAST", "value": "1"},
        ],
    },
    {
        "variable": "btn,PHOTOVOLTAIC",
        "entity_id": "select.iotmeter_pv_mode",
        "unique_id": "iotmeter_pv_mode",
        "name": "IoTmeter PV Mode",
        "options": [
            {"label": "Off", "value": "0"},
            {"label": "1p", "value": "1"},
            {"label": "3p", "value": "2"},
        ],
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities,
) -> None:
    """Set up IoTMeter select entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: IoTMeterCoordinator = data["coordinator"]

    entities: list[IoTMeterSelectSetting] = [
        IoTMeterSelectSetting(
            coordinator=coordinator,
            config_entry_id=entry.entry_id,
            variable=cfg["variable"],
            entity_id=cfg["entity_id"],
            unique_id=cfg["unique_id"],
            name=cfg["name"],
            options_cfg=cfg["options"],
        )
        for cfg in SELECT_SETTINGS
    ]

    async_add_entities(entities)


class IoTMeterSelectSetting(CoordinatorEntity, SelectEntity):
    """Select napojený na /updateSetting."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: IoTMeterCoordinator,
        config_entry_id: str,
        variable: str,
        entity_id: str,
        unique_id: str,
        name: str,
        options_cfg: list[dict[str, str]],
    ) -> None:
        super().__init__(coordinator)
        self._config_entry_id = config_entry_id
        self._variable = variable

        self.entity_id = entity_id
        self._attr_unique_id = unique_id
        self._attr_name = name

        # mapování label <-> value
        self._options_cfg = options_cfg
        self._label_to_value = {o["label"]: o["value"] for o in options_cfg}
        self._value_to_label = {o["value"]: o["label"] for o in options_cfg}
        self._attr_options = [o["label"] for o in options_cfg]

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

    @property
    def current_option(self) -> str | None:
        """Aktuální textová volba (ECO/FAST/Off/1p/3p)."""
        raw_val = self._settings.get(self._variable)
        if raw_val is None:
            return None
        label = self._value_to_label.get(str(raw_val))
        return label

    async def async_select_option(self, option: str) -> None:
        """Změna volby → POST /updateSetting."""
        if option not in self._label_to_value:
            _LOGGER.warning("IoTMeter: neznámá volba %s pro %s", option, self._variable)
            return

        value = self._label_to_value[option]

        hass = self.hass
        ip = self.coordinator.ip_address
        port = self.coordinator.port

        url = f"http://{ip}:{port}/updateSetting"
        session = async_get_clientsession(hass)

        payload = {
            "variable": self._variable,
            "value": str(value),
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
                    "IoTMeter: nastavení %s = %s (%s) OK: %s",
                    self._variable,
                    value,
                    option,
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
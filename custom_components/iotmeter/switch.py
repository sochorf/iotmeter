from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import IoTMeterCoordinator

_LOGGER = logging.getLogger(__name__)

# Konfigurace všech boolean nastavení, která chceme z HA měnit
SWITCH_SETTINGS: list[dict[str, str]] = [
    {
        "variable": "sw,WHEN AC IN: CHARGING",
        "entity_id": "switch.iotmeter_hdo_charging",
        "unique_id": "iotmeter_hdo_charging",
        "name": "IoTmeter HDO Charging",
    },
    {
        "variable": "sw,ENABLE CHARGING",
        "entity_id": "switch.iotmeter_enable_charging",
        "unique_id": "iotmeter_enable_charging",
        "name": "IoTmeter Enable Charging",
    },
    {
        "variable": "sw,ENABLE BALANCING",
        "entity_id": "switch.iotmeter_enable_balancing",
        "unique_id": "iotmeter_enable_balancing",
        "name": "IoTmeter Enable Balancing",
    },
    {
        "variable": "sw,WHEN AC IN: RELAY ON",
        "entity_id": "switch.iotmeter_relay_on_ac_in",
        "unique_id": "iotmeter_relay_on_ac_in",
        "name": "IoTmeter Relay on AC IN",
    },
    {
        "variable": "sw,WHEN OVERFLOW: RELAY ON",
        "entity_id": "switch.iotmeter_relay_on_overflow",
        "unique_id": "iotmeter_relay_on_overflow",
        "name": "IoTmeter Relay on Overflow",
    },
    {
        "variable": "sw,AC IN ACTIVE: HIGH",
        "entity_id": "switch.iotmeter_ac_in_active_high",
        "unique_id": "iotmeter_ac_in_active_high",
        "name": "IoTmeter AC IN Active High",
    },
    {
        "variable": "sw,P-E15-GUARD",
        "entity_id": "switch.iotmeter_p_e15_guard",
        "unique_id": "iotmeter_p_e15_guard",
        "name": "IoTmeter P E15 Guard",
    },
]


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up IoTMeter switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: IoTMeterCoordinator = data["coordinator"]

    entities: list[IoTMeterBoolSettingSwitch] = [
        IoTMeterBoolSettingSwitch(
            coordinator=coordinator,
            config_entry_id=entry.entry_id,
            variable=cfg["variable"],
            entity_id=cfg["entity_id"],
            unique_id=cfg["unique_id"],
            name=cfg["name"],
        )
        for cfg in SWITCH_SETTINGS
    ]

    async_add_entities(entities)


class IoTMeterBoolSettingSwitch(CoordinatorEntity, SwitchEntity):
    """Obecný switch pro bool nastavení v /updateSetting (0/1)."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: IoTMeterCoordinator,
        config_entry_id: str,
        variable: str,
        entity_id: str,
        unique_id: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry_id = config_entry_id
        self._variable = variable

        self.entity_id = entity_id
        self._attr_unique_id = unique_id
        self._attr_name = name

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)},
            name="IoTMeter",
            manufacturer="IoTMeter",
            model="REST-based energy meter",
        )

    # --- pomocné metody --------------------------------------------------

    @property
    def _settings(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return data.get("settings") or {}

    def _to_int(self, value: Any) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    # --- stav switch entity ----------------------------------------------

    @property
    def is_on(self) -> bool | None:
        """True = hodnota nastavení == 1."""
        value = self._to_int(self._settings.get(self._variable))
        if value is None:
            return None
        return value == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_flag(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_flag(0)

    async def _async_set_flag(self, value: int) -> None:
        """POST /updateSetting s JSON {'variable': ..., 'value': '0'/'1'}."""
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
                    "IoTMeter: nastavení %s = %s OK: %s",
                    self._variable,
                    value,
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
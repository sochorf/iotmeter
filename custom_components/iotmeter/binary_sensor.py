from __future__ import annotations

from typing import Any
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IoTMeterCoordinator
from .entity_definitions import (
    BINARY_SENSOR_DEFINITIONS,
    IoTMeterBinarySensorDescription,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up IoTMeter binary sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: IoTMeterCoordinator = data["coordinator"]

    entities: list[IoTMeterBinarySensorEntity] = []
    for desc in BINARY_SENSOR_DEFINITIONS.values():
        entities.append(IoTMeterBinarySensorEntity(coordinator, desc, entry.entry_id))

    async_add_entities(entities)

    # Přidáváme entity i po pozdějším úspěšném čtení, pokud API při startu selhalo.
    # Při snížení počtu staré entity nemažeme: stanou se unavailable.
    created_evse = set()

    def add_evse_entities():
        count = coordinator.evse_count()
        if count is None:
            return
        additions = []
        for index in range(count):
            if index in created_evse:
                continue
            created_evse.add(index)
            additions.append(IoTMeterEVSEConnected(coordinator, entry.entry_id, index))
        if additions:
            async_add_entities(additions)

    add_evse_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_evse_entities))



class IoTMeterBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Reprezentuje jeden IoTMeter binary senzor."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: IoTMeterCoordinator,
        description: IoTMeterBinarySensorDescription,
        config_entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._config_entry_id = config_entry_id

        self.entity_id = f"binary_sensor.{description.entity_id}"
        self._attr_unique_id = description.entity_id
        self._attr_name = description.name

        if description.device_class:
            self._attr_device_class = description.device_class

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)},
            name="IoTMeter",
            manufacturer="IoTMeter",
            model="REST-based energy meter",
        )

    # ---------------------------------------------------------------------
    #  Helper: zdrojová data
    # ---------------------------------------------------------------------

    def _get_block(self, source: str) -> dict[str, Any]:
        data = self.coordinator.data or {}
        if source == "settings":
            return data.get("settings") or {}
        if source == "evse":
            return data.get("evse") or {}
        if source == "data":
            return data.get("data") or {}
        return {}

    def _to_int(self, value: Any) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    # ---------------------------------------------------------------------
    #  CALC LOGIKA
    # ---------------------------------------------------------------------

    def _calc_hdo_state(self) -> bool | None:
        """Původně: is_state('sensor.iotmeter_ac_in_state','true').

        Tady uděláme to samé přímo z registru A:
          A == 1 -> True
          A == 0 -> False
        Jinak None.
        """
        data_block = self._get_block("data")
        v = self._to_int(data_block.get("A"))
        if v is None:
            return None
        if v == 1:
            return True
        if v == 0:
            return False
        return None

    def _calc_hdo_charging(self) -> bool | None:
        """Původně: is_state('sensor.iotmeter_enable_ac_in_charging','true').

        Tady přímo z nastavení:
          sw,WHEN AC IN: CHARGING == 1 -> True
          == 0 -> False
        """
        settings = self._get_block("settings")
        v = self._to_int(settings.get("sw,WHEN AC IN: CHARGING"))
        if v is None:
            return None
        if v == 1:
            return True
        if v == 0:
            return False
        return None

    # ---------------------------------------------------------------------
    #  BINARY SENSOR API
    # ---------------------------------------------------------------------

    @property
    def is_on(self) -> bool | None:
        """Vrací True/False podle calc logiky."""
        if not self.coordinator.data:
            return None

        calc = self._description.calc

        if calc == "hdo_state":
            return self._calc_hdo_state()

        if calc == "hdo_charging":
            return self._calc_hdo_charging()

        _LOGGER.debug("IoTMeter: neznámý binary calc '%s' pro %s", calc, self._description.entity_id)
        return None

class IoTMeterEVSEConnected(CoordinatorEntity, BinarySensorEntity):
    """Připojení vozu pouze podle ověřených kódů 1/2.

    Neověřený kód může znamenat i nabíjení: nesmí být interpretován jako off.
    Proto je při jiném kódu připojení unavailable a raw kód zůstává v senzoru.
    """

    _attr_should_poll = False
    _attr_device_class = "plug"

    def __init__(self, coordinator, entry_id, index):
        super().__init__(coordinator)
        self._index = index
        suffix = f"iotmeter_evse{index + 1}_connected"
        self.entity_id = f"binary_sensor.{suffix}"
        self._attr_unique_id = f"{entry_id}_{suffix}"
        self._attr_name = f"IoTMeter EVSE{index + 1} Connected"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)}, name="IoTMeter",
            manufacturer="IoTMeter", model="REST-based energy meter",
        )

    @property
    def available(self):
        return self.coordinator.evse_value(self._index, "EV_STATE") in (1, 2)

    @property
    def is_on(self):
        raw = self.coordinator.evse_value(self._index, "EV_STATE")
        return raw == 2 if raw in (1, 2) else None

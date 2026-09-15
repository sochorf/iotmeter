from __future__ import annotations

from typing import Any, Optional
import logging
import math
from decimal import Decimal, InvalidOperation

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import IoTMeterCoordinator
from .entity_definitions import (
    SENSOR_DEFINITIONS,
    IoTMeterSensorDescription,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up IoTMeter sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: IoTMeterCoordinator = data["coordinator"]

    entities: list[IoTMeterSensorEntity] = []
    for desc in SENSOR_DEFINITIONS.values():
        entities.append(IoTMeterSensorEntity(coordinator, desc, entry.entry_id))

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
            for kind in ("state", "state_code", "comm_err", "config_current", "output_current"):
                additions.append(IoTMeterEVSESensor(coordinator, entry.entry_id, index, kind))
        if additions:
            async_add_entities(additions)

    add_evse_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_evse_entities))



class IoTMeterSensorEntity(CoordinatorEntity, SensorEntity):
    """Reprezentuje jeden IoTMeter senzor (podle definice v SENSOR_DEFINITIONS)."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: IoTMeterCoordinator,
        description: IoTMeterSensorDescription,
        config_entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._config_entry_id = config_entry_id

        # Zachováme původní entity_id a unique_id
        self.entity_id = f"sensor.{description.entity_id}"
        self._attr_unique_id = description.entity_id
        self._attr_name = description.name

        # Device class & unit (převezmeme z definice, pokud je)
        if description.device_class:
            # starší HA používá string; moderní má konstanty – ale stringy fungují
            self._attr_device_class = description.device_class

        if description.unit:
            self._attr_native_unit_of_measurement = description.unit

        if description.state_class:
            self._attr_state_class = description.state_class

        # Info o zařízení – všechny entity do jednoho "IoTMeter" zařízení
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)},
            name="IoTMeter",
            manufacturer="IoTMeter",
            model="REST-based energy meter",
        )

    # ---------------------------------------------------------------------
    #  DATA HELPERY
    # ---------------------------------------------------------------------

    def _get_block(self, source: str) -> dict[str, Any]:
        """Vrátí blok dat podle zdroje (settings / evse / data / derived)."""
        data = self.coordinator.data or {}
        if source == "settings":
            return data.get("settings") or {}
        if source == "evse":
            return data.get("evse") or {}
        if source == "data":
            return data.get("data") or {}
        # "derived" – používá se jen v calc; tady vrátíme prázdné
        return {}

    def _to_int(self, value: Any) -> Optional[int]:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def _transform_value(self, raw: Any, transform: Optional[str]) -> Any:
        """Aplikuje pojmenovanou transformaci na raw hodnotu."""
        if raw is None:
            return None
        if not transform:
            return raw

        if transform == "int":
            return self._to_int(raw)

        if transform == "int_100_div":
            iv = self._to_int(raw)
            if iv is None:
                return None
            return iv / 100

        if transform == "signed_16bit":
            iv = self._to_int(raw)
            if iv is None:
                return None
            if iv > 32767:
                iv = iv - 65536
            return iv

        if transform == "signed_16bit_100_div":
            iv = self._to_int(raw)
            if iv is None:
                return None
            if iv > 32767:
                iv = iv - 65536
            return iv / 100

        if transform == "list_index_1_int":
            # očekává se seznam, vezmeme index 1
            if isinstance(raw, (list, tuple)) and len(raw) > 1:
                return self._to_int(raw[1])
            return None

        # default – neznámá transformace, vrátíme raw
        _LOGGER.debug("IoTMeter: neznámá transformace '%s', vracím raw", transform)
        return raw

    # ---------------------------------------------------------------------
    #  CALC HELPERY – pro derived senzory
    # ---------------------------------------------------------------------

    def _calc_iotm_s_last(self) -> Any:
        """Poslední skutečně úspěšná odpověď SETTINGS, nebo None."""
        return self.coordinator.last_success["settings"]

    def _calc_iotm_d_last(self) -> Any:
        """Poslední skutečně úspěšná odpověď DATA, nebo None."""
        return self.coordinator.last_success["data"]

    def _calc_charging_mode(self) -> str:
        settings = self._get_block("settings")
        v = self._to_int(settings.get("chargeMode"))
        if v == 0:
            return "ECO"
        if v == 1:
            return "FAST"
        return "I dont know"

    def _calc_enable_charging(self) -> str:
        settings = self._get_block("settings")
        v = self._to_int(settings.get("sw,ENABLE CHARGING"))
        if v == 0:
            return "false"
        if v == 1:
            return "true"
        return "I dont know"

    def _calc_ac_in_state(self) -> str:
        data_block = self._get_block("data")
        v = self._to_int(data_block.get("A"))
        if v == 0:
            return "false"
        if v == 1:
            return "true"
        return "I dont know"

    def _calc_enable_ac_in_charging(self) -> str:
        settings = self._get_block("settings")
        v = self._to_int(settings.get("sw,WHEN AC IN: CHARGING"))
        if v == 0:
            return "false"
        if v == 1:
            return "true"
        return "I dont know"

    def _calc_enable_balancing(self) -> str:
        settings = self._get_block("settings")
        v = self._to_int(settings.get("sw,ENABLE BALANCING"))
        if v == 0:
            return "false"
        if v == 1:
            return "true"
        return "I dont know"

    def _calc_fve_support_mode(self) -> str:
        settings = self._get_block("settings")
        v = self._to_int(settings.get("btn,PHOTOVOLTAIC"))
        if v == 0:
            return "Off"
        if v == 1:
            return "1p"
        if v == 2:
            return "3p"
        return "I dont know"

    def _calc_pv_grid_assist(self) -> Optional[int]:
        settings = self._get_block("settings")
        return self._to_int(settings.get("in,PV-GRID-ASSIST-A"))

    def _calc_errors(self) -> Optional[int]:
        settings = self._get_block("settings")
        return self._to_int(settings.get("ERRORS"))

    def _sum_valid_phases(self, keys: tuple[str, str, str], *, power: bool = False) -> Optional[int]:
        """Součet tří surových celočíselných polí z jedné odpovědi DATA.

        Chybějící nebo neplatná fáze zneplatní celý součet. Skutečná nula
        je platná. Nepřevádíme unknown/None/NaN na nulu ani desetinné
        hodnoty na celé oříznutím. Přijímáme JSON čísla i číselné řetězce.
        Výkon zachovává dosavadní dekódování signed 16 bit: raw 32768–65535
        převedeme na zápornou hodnotu. Již záporné signed hodnoty ponecháme.
        Energetická pole jsou nezáporné čítače; jejich rozsah shora neměníme.
        """
        data = self._get_block("data")
        values = []
        for key in keys:
            raw = data.get(key)
            if raw is None or isinstance(raw, bool):
                return None
            try:
                # Decimal zachová přesnost i větších celočíselných čítačů.
                number = Decimal(str(raw))
                if not number.is_finite() or number != number.to_integral_value():
                    return None
                value = int(number)
            except (InvalidOperation, TypeError, ValueError, OverflowError):
                return None
            if power:
                if not -32768 <= value <= 65535:
                    return None
                if value > 32767:
                    value -= 65536
            elif value < 0:
                return None
            values.append(value)
        return sum(values)

    def _calc_sum_import_today(self) -> Optional[float]:
        value = self._sum_valid_phases(("E1dP", "E2dP", "E3dP"))
        return value / 100 if value is not None else None

    def _calc_sum_import_total(self) -> Optional[float]:
        value = self._sum_valid_phases(("E1tP", "E2tP", "E3tP"))
        return value / 100 if value is not None else None

    def _calc_sum_export_today(self) -> Optional[float]:
        value = self._sum_valid_phases(("E1dN", "E2dN", "E3dN"))
        return value / 100 if value is not None else None

    def _calc_sum_export_total(self) -> Optional[float]:
        value = self._sum_valid_phases(("E1tN", "E2tN", "E3tN"))
        return value / 100 if value is not None else None

    def _calc_sum_p123(self) -> Optional[int]:
        return self._sum_valid_phases(("P1", "P2", "P3"), power=True)

    def _calc_evse_today_energy(self) -> Optional[float]:
        """Replika původního templatu – rozdíl mezi IoTMeter Today Import a Wattsonic grid purchasing."""
        # a = states('sensor.iotmeter_today_import_energy')
        # b = states('sensor.wattsonic_grid_purchasing_energy_on_that_day')
        hass = self.hass
        if hass is None:
            return None
        s_iot = hass.states.get("sensor.iotmeter_today_import_energy")
        s_ws = hass.states.get("sensor.wattsonic_grid_purchasing_energy_on_that_day")

        try:
            a = float(s_iot.state) if s_iot and s_iot.state not in (None, "", "unknown", "unavailable") else 0.0
        except (TypeError, ValueError):
            a = 0.0
        try:
            b = float(s_ws.state) if s_ws and s_ws.state not in (None, "", "unknown", "unavailable") else 0.0
        except (TypeError, ValueError):
            b = 0.0

        diff = a - b
        if diff > 0:
            return diff
        return 0.0

    def _calc_ev_charger_p(self) -> Optional[int]:
        """Odhad příkonu větve obou wallboxů včetně jejich vlastní spotřeby.

        Rozdíl dvou měřidel v W, se shodnou znaménkovou konvencí.
        Odečty nejsou synchronní; zápornou odchylku nezakrýváme nulou.
        Název a unique_id zůstávají kvůli existujícím vazbám zachované."""
        hass = self.hass
        if hass is None:
            return None

        # náš senzor iotmeter_p_sum
        s_iot = hass.states.get("sensor.iotmeter_p_sum")
        s_ws = hass.states.get("sensor.wattsonic_total_power_on_meter_w")

        try:
            a = int(float(s_iot.state)) if s_iot and s_iot.state not in (None, "", "unknown", "unavailable") else 0
        except (TypeError, ValueError):
            a = 0
        try:
            b = int(float(s_ws.state)) if s_ws and s_ws.state not in (None, "", "unknown", "unavailable") else 0
        except (TypeError, ValueError):
            b = 0

        return a - b

    # ---------------------------------------------------------------------
    #  HODNOTA SENZORU
    # ---------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Dostupnost podle endpointu, nikoli podle přítomnosti cache.

        Výpočty a jejich entity_id zatím neměníme. U dvou odhadů auta
        navíc odmítneme chybějící/nečíselné externí vstupy; nespravujeme
        zde jejich názvy, znaménka ani nesprávnou energetickou metodiku.
        """
        desc = self._description
        if desc.calc in ("iotm_s_last", "iotm_d_last"):
            return True  # před prvním úspěchem unknown, při chybě poslední čas
        source = desc.source
        if desc.calc:
            if desc.calc in (
                "charging_mode", "enable_charging", "enable_ac_in_charging",
                "enable_balancing", "fve_support_mode", "pv_grid_assist", "errors",
            ):
                source = "settings"
            elif desc.calc in (
                "ac_in_state", "sum_import_today", "sum_import_total",
                "sum_export_today", "sum_export_total", "sum_p123",
                "evse_today_energy", "ev_charger_p",
            ):
                source = "data"
            else:
                return False  # nová calc funkce musí výslovně určit závislost
        if not self.coordinator.last_update_success or not self.coordinator.source_success.get(source, False):
            return False
        # Úspěšný HTTP dotaz s ID ještě nezaručuje všechna měřicí pole.
        # Ověřujeme stejným výpočtem jako native_value: neplatný součet
        # bude unavailable, nikoli nula ani částečný součet.
        sum_calculations = {
            "sum_import_today": self._calc_sum_import_today,
            "sum_import_total": self._calc_sum_import_total,
            "sum_export_today": self._calc_sum_export_today,
            "sum_export_total": self._calc_sum_export_total,
            "sum_p123": self._calc_sum_p123,
        }
        calculation = sum_calculations.get(desc.calc)
        if calculation is not None and calculation() is None:
            return False
        # Odhady auta nesmějí použít neúplný součet ani během aktualizace
        # ostatních entit, kdy jejich publikovaný stav může být ještě starý.
        if desc.calc == "ev_charger_p" and self._calc_sum_p123() is None:
            return False
        if desc.calc == "evse_today_energy" and self._calc_sum_import_today() is None:
            return False
        dependencies = {
            "evse_today_energy": (
                "sensor.iotmeter_today_import_energy",
                "sensor.wattsonic_grid_purchasing_energy_on_that_day",
            ),
            "ev_charger_p": (
                "sensor.iotmeter_p_sum", "sensor.wattsonic_total_power_on_meter_w",
            ),
        }
        for entity_id in dependencies.get(desc.calc, ()):
            state = self.hass.states.get(entity_id) if self.hass else None
            try:
                if state is None or not math.isfinite(float(state.state)):
                    return False
            except (TypeError, ValueError):
                return False
        return True

    @property
    def native_value(self) -> Any:
        """Vrací aktuální hodnotu senzoru podle definice."""
        desc = self._description

        # Pokud není žádná data (zatím se nerefreshlo), vrať None
        if not self.coordinator.data:
            return None

        # 1) Derived senzory (calc funkce)
        if desc.calc:
            calc_name = desc.calc

            if calc_name == "iotm_s_last":
                return self._calc_iotm_s_last()
            if calc_name == "iotm_d_last":
                return self._calc_iotm_d_last()
            if calc_name == "charging_mode":
                return self._calc_charging_mode()
            if calc_name == "enable_charging":
                return self._calc_enable_charging()
            if calc_name == "ac_in_state":
                return self._calc_ac_in_state()
            if calc_name == "enable_ac_in_charging":
                return self._calc_enable_ac_in_charging()
            if calc_name == "enable_balancing":
                return self._calc_enable_balancing()
            if calc_name == "fve_support_mode":
                return self._calc_fve_support_mode()
            if calc_name == "pv_grid_assist":
                return self._calc_pv_grid_assist()
            if calc_name == "errors":
                return self._calc_errors()
            if calc_name == "sum_import_today":
                return self._calc_sum_import_today()
            if calc_name == "sum_import_total":
                return self._calc_sum_import_total()
            if calc_name == "sum_export_today":
                return self._calc_sum_export_today()
            if calc_name == "sum_export_total":
                return self._calc_sum_export_total()
            if calc_name == "sum_p123":
                return self._calc_sum_p123()
            if calc_name == "evse_today_energy":
                return self._calc_evse_today_energy()
            if calc_name == "ev_charger_p":
                return self._calc_ev_charger_p()

            _LOGGER.debug("IoTMeter: neznámý calc '%s' pro %s", calc_name, desc.entity_id)
            return None

        # 2) Normální senzory (zdroj + key + transform)
        block = self._get_block(desc.source)
        if not desc.key:
            return None

        raw = block.get(desc.key)
        return self._transform_value(raw, desc.transform)

    # ---------------------------------------------------------------------
    #  ATTRIBUTES – speciálně pro iotm_s_last a iotm_d_last
    # ---------------------------------------------------------------------

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        desc = self._description
        attrs: dict[str, Any] = {}

        if not self.coordinator.data:
            return attrs

        # iotm_s_last – atributy z "settings"
        if desc.calc == "iotm_s_last":
            settings = self._get_block("settings")
            if settings:
                attrs["chargeMode"] = settings.get("chargeMode")
                attrs["enableCharge"] = settings.get("sw,ENABLE CHARGING")
                attrs["pv_grid_assist"] = settings.get("in,PV-GRID-ASSIST-A")
                attrs["errors"] = settings.get("ERRORS")
                attrs["enable_balancing"] = settings.get("sw,ENABLE BALANCING")
                attrs["enable_ac_in_charging"] = settings.get("sw,WHEN AC IN: CHARGING")
                attrs["pv_mode"] = settings.get("btn,PHOTOVOLTAIC")

        # iotm_d_last – atributy z "data"
        if desc.calc == "iotm_d_last":
            data_block = self._get_block("data")
            # Zkopíruj vybrané klíče, které odpovídají původním atributům
            for key in (
                "A",
                "E1dN",
                "E2dN",
                "E3dN",
                "E1dP",
                "E2dP",
                "E3dP",
                "E1tN",
                "E2tN",
                "E3tN",
                "E1tP",
                "E2tP",
                "E3tP",
                "R1",
                "R2",
                "R3",
                "W1",
                "W2",
                "W3",
            ):
                if key in data_block:
                    attrs[key] = data_block.get(key)

        return attrs

class IoTMeterEVSESensor(CoordinatorEntity, SensorEntity):
    """Per-wallbox read-only diagnostika; stávající společné senzory zachovány."""

    _attr_should_poll = False
    _KEYS = {
        "state": "EV_STATE", "state_code": "EV_STATE",
        "comm_err": "EV_COMM_ERR", "config_current": "ACTUAL_CONFIG_CURRENT",
        "output_current": "ACTUAL_OUTPUT_CURRENT",
    }

    def __init__(self, coordinator, entry_id, index, kind):
        super().__init__(coordinator)
        self._index = index
        self._kind = kind
        suffix = f"iotmeter_evse{index + 1}_{kind}"
        self.entity_id = f"sensor.{suffix}"
        self._attr_unique_id = f"{entry_id}_{suffix}"
        self._attr_name = f"IoTMeter EVSE{index + 1} {kind.replace('_', ' ').title()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)}, name="IoTMeter",
            manufacturer="IoTMeter", model="REST-based energy meter",
        )
        if kind in ("config_current", "output_current"):
            self._attr_native_unit_of_measurement = "A"
            self._attr_device_class = "current"
        # Záměrně žádné state_class: proudové údaje nejsou ověřené měření odběru.

    @property
    def available(self):
        return self.coordinator.evse_value(self._index, self._KEYS[self._kind]) is not None

    @property
    def native_value(self):
        raw = self.coordinator.evse_value(self._index, self._KEYS[self._kind])
        if raw is None:
            return None
        if self._kind == "state":
            return {1: "disconnected", 2: "connected"}.get(raw, "unmapped")
        return raw

    @property
    def extra_state_attributes(self):
        stamp = self.coordinator.last_success.get("evse")
        return {
            "wallbox_number": self._index + 1,
            "source_key": self._KEYS[self._kind],
            "raw_value": self.coordinator.evse_value(self._index, self._KEYS[self._kind]),
            "last_success": stamp.isoformat() if stamp else None,
        }

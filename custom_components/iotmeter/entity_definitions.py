from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


SensorSource = Literal["settings", "evse", "data", "derived"]


@dataclass(frozen=True)
class IoTMeterSensorDescription:
    """Popis jednoho senzoru IoTMeteru."""

    # entity_id bez prefixu "sensor.", např. "iotmeter_u1"
    entity_id: str

    # Zobrazovaný název v HA
    name: str

    # Z jakého zdroje pochází primární data
    #  - "settings" => coordinator.data["settings"]
    #  - "evse"     => coordinator.data["evse"]
    #  - "data"     => coordinator.data["data"]
    #  - "derived"  => počítá se z více zdrojů / jiných entit
    source: SensorSource = "data"

    # Primární klíč v JSONu (např. "U1", "E1dP", ...)
    # Pro derived senzory může být None
    key: Optional[str] = None

    # Device class / state_class / unit
    device_class: Optional[str] = None
    state_class: Optional[str] = None
    unit: Optional[str] = None

    # Jméno "typové" transformace, kterou si implementujeme v sensor.py
    transform: Optional[str] = None

    # Interní identifikátor pro speciální výpočty (např. iotm_s_last, iotm_d_last, evse_today_energy)
    calc: Optional[str] = None


@dataclass(frozen=True)
class IoTMeterBinarySensorDescription:
    """Popis jednoho binary senzoru IoTMeteru."""

    entity_id: str
    name: str
    source: SensorSource = "derived"
    # jméno speciálního výpočtu v binary_sensor.py (např. "hdo_state")
    calc: Optional[str] = None
    device_class: Optional[str] = None


###############################################################################
#  SENSOR DEFINITIONS – všechny entity z původního package (FULL režim)
###############################################################################

SENSOR_DEFINITIONS: dict[str, IoTMeterSensorDescription] = {
    # ---------------------------------------------------------------------
    # SETTINGS – last good result + atributy
    # ---------------------------------------------------------------------
    "iotm_s_last": IoTMeterSensorDescription(
        entity_id="iotm_s_last",
        name="IOTmeter Settings last good result",
        source="derived",
        calc="iotm_s_last",
    ),

    # ---------------------------------------------------------------------
    # EVSE
    # ---------------------------------------------------------------------
    "iotm_evse_count": IoTMeterSensorDescription(
        entity_id="iotm_evse_count",
        name="IOTmeter Number of EVSE",
        source="evse",
        key="NUMBER_OF_EVSE",
        transform="int",
    ),
    "iotm_evse_actual_output_current": IoTMeterSensorDescription(
        entity_id="iotm_evse_actual_output_current",
        name="IOTmeter Actual EVSE Output Current",
        source="evse",
        key="ACTUAL_OUTPUT_CURRENT",
        device_class="current",
        unit="A",
        transform="list_index_1_int",
    ),
    "iotm_evse_actual_config_current": IoTMeterSensorDescription(
        entity_id="iotm_evse_actual_config_current",
        name="IOTmeter Actual EVSE Config Current",
        source="evse",
        key="ACTUAL_CONFIG_CURRENT",
        device_class="current",
        unit="A",
        transform="list_index_1_int",
    ),

    # ---------------------------------------------------------------------
    # DATA – last good result + atributy
    # ---------------------------------------------------------------------
    "iotm_d_last": IoTMeterSensorDescription(
        entity_id="iotm_d_last",
        name="IOTmeter Data last good result",
        source="derived",
        calc="iotm_d_last",
    ),

    # ---------------------------------------------------------------------
    # VOLTAGES U1–U3
    # ---------------------------------------------------------------------
    "iotmeter_u1": IoTMeterSensorDescription(
        entity_id="iotmeter_u1",
        name="IoTmeter U1",
        source="data",
        key="U1",
        device_class="voltage",
        unit="V",
        transform="int",
    ),
    "iotmeter_u2": IoTMeterSensorDescription(
        entity_id="iotmeter_u2",
        name="IoTmeter U2",
        source="data",
        key="U2",
        device_class="voltage",
        unit="V",
        transform="int",
    ),
    "iotmeter_u3": IoTMeterSensorDescription(
        entity_id="iotmeter_u3",
        name="IoTmeter U3",
        source="data",
        key="U3",
        device_class="voltage",
        unit="V",
        transform="int",
    ),

    # ---------------------------------------------------------------------
    # POWER FACTOR F1–F3
    # ---------------------------------------------------------------------
    "iotmeter_f1": IoTMeterSensorDescription(
        entity_id="iotmeter_f1",
        name="IoTmeter Power Factor L1",
        source="data",
        key="F1",
        device_class="power_factor",
        transform="int_100_div",
    ),
    "iotmeter_f2": IoTMeterSensorDescription(
        entity_id="iotmeter_f2",
        name="IoTmeter Power Factor L2",
        source="data",
        key="F2",
        device_class="power_factor",
        transform="int_100_div",
    ),
    "iotmeter_f3": IoTMeterSensorDescription(
        entity_id="iotmeter_f3",
        name="IoTmeter Power Factor L3",
        source="data",
        key="F3",
        device_class="power_factor",
        transform="int_100_div",
    ),

    # ---------------------------------------------------------------------
    # TODAY MAX EXPORT / IMPORT POWER – R1/R2/R3, W1/W2/W3
    # ---------------------------------------------------------------------
    "iotmeter_tmep1": IoTMeterSensorDescription(
        entity_id="iotmeter_tmep1",
        name="IoTmeter Today Max Export Power L1",
        source="data",
        key="R1",
        device_class="power",
        unit="W",
        transform="int",
    ),
    "iotmeter_tmep2": IoTMeterSensorDescription(
        entity_id="iotmeter_tmep2",
        name="IoTmeter Today Max Export Power L2",
        source="data",
        key="R2",
        device_class="power",
        unit="W",
        transform="int",
    ),
    "iotmeter_tmep3": IoTMeterSensorDescription(
        entity_id="iotmeter_tmep3",
        name="IoTmeter Today Max Export Power L3",
        source="data",
        key="R3",
        device_class="power",
        unit="W",
        transform="int",
    ),
    "iotmeter_tmip1": IoTMeterSensorDescription(
        entity_id="iotmeter_tmip1",
        name="IoTmeter Today Max Import Power L1",
        source="data",
        key="W1",
        device_class="power",
        unit="W",
        transform="int",
    ),
    "iotmeter_tmip2": IoTMeterSensorDescription(
        entity_id="iotmeter_tmip2",
        name="IoTmeter Today Max Import Power L2",
        source="data",
        key="W2",
        device_class="power",
        unit="W",
        transform="int",
    ),
    "iotmeter_tmip3": IoTMeterSensorDescription(
        entity_id="iotmeter_tmip3",
        name="IoTmeter Today Max Import Power L3",
        source="data",
        key="W3",
        device_class="power",
        unit="W",
        transform="int",
    ),

    # ---------------------------------------------------------------------
    # OPTIONS – charging mode, enable charging, AC in, FVE mode, atd.
    # ---------------------------------------------------------------------
    "iotmeter_charging_mode": IoTMeterSensorDescription(
        entity_id="iotmeter_charging_mode",
        name="IoTmeter Charging Mode",
        source="derived",
        calc="charging_mode",
    ),
    "iotmeter_enable_charging": IoTMeterSensorDescription(
        entity_id="iotmeter_enable_charging",
        name="IoTmeter Enable Charging",
        source="derived",
        calc="enable_charging",
    ),
    "iotmeter_ac_in_state": IoTMeterSensorDescription(
        entity_id="iotmeter_ac_in_state",
        name="IoTmeter AC in State",
        source="derived",
        calc="ac_in_state",
    ),
    "iotmeter_enable_ac_in_charging": IoTMeterSensorDescription(
        entity_id="iotmeter_enable_ac_in_charging",
        name="IoTmeter Enable AC IN Charging",
        source="derived",
        calc="enable_ac_in_charging",
    ),
    "iotmeter_enable_balancing": IoTMeterSensorDescription(
        entity_id="iotmeter_enable_balancing",
        name="IoTmeter Enable Balancing",
        source="derived",
        calc="enable_balancing",
    ),
    "iotmeter_fve_support_mode": IoTMeterSensorDescription(
        entity_id="iotmeter_fve_support_mode",
        name="IoTmeter FVE support mode",
        source="derived",
        calc="fve_support_mode",
    ),
    "iotmeter_max_current_from_grid": IoTMeterSensorDescription(
        entity_id="iotmeter_max_current_from_grid",
        name="IoTmeter max current from grid",
        source="settings",
        key="in,MAX-CURRENT-FROM-GRID-A",
        device_class="current",
        unit="A",
        transform="int",
    ),
    "iotmeter_max_current_from_grid_hdo": IoTMeterSensorDescription(
        entity_id="iotmeter_max_current_from_grid_hdo",
        name="IoTmeter max current from grid on HDO",
        source="settings",
        key="in,AC-IN-MAX-CURRENT-FROM-GRID-A",
        device_class="current",
        unit="A",
        transform="int",
    ),
    "iotmeter_pv_grid_assist": IoTMeterSensorDescription(
        entity_id="iotmeter_pv_grid_assist",
        name="IoTmeter PV Grid Assist",
        source="derived",
        calc="pv_grid_assist",
        device_class="current",
        unit="A",
    ),
    "iotmmeter_errors": IoTMeterSensorDescription(
        entity_id="iotmmeter_errors",
        name="IoTmeter Errors",
        source="derived",
        calc="errors",
    ),
    "iotmmeter_sw_version": IoTMeterSensorDescription(
        entity_id="iotmmeter_sw_version",
        name="IoTmeter Firmware Version",
        source="settings",
        key="txt,ACTUAL SW VERSION",
    ),

    # ---------------------------------------------------------------------
    # ENERGY – import/export today/total (L1, L2, L3, sum)
    # ---------------------------------------------------------------------
    "iotmeter_ie1": IoTMeterSensorDescription(
        entity_id="iotmeter_ie1",
        name="IoTmeter Today Import Energy L1",
        source="data",
        key="E1dP",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_ie2": IoTMeterSensorDescription(
        entity_id="iotmeter_ie2",
        name="IoTmeter Today Import Energy L2",
        source="data",
        key="E2dP",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_ie3": IoTMeterSensorDescription(
        entity_id="iotmeter_ie3",
        name="IoTmeter Today Import Energy L3",
        source="data",
        key="E3dP",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_ie": IoTMeterSensorDescription(
        entity_id="iotmeter_ie",
        name="IoTmeter Today Import Energy",
        source="derived",
        calc="sum_import_today",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
    ),
    "iotmeter_iep": IoTMeterSensorDescription(
        entity_id="iotmeter_iep",
        name="IoTmeter Yesterday Imported Energy",
        source="data",
        key="EpDP",
        device_class="energy",
        # Včerejší energie je denní výsledek, nikoli rostoucí čítač.
        # Bez state_class: běžná historie zůstává, nové dlouhodobé statistiky nevznikají.
        unit="kWh",
        transform="int_100_div",
    ),
    "evse_today_energy": IoTMeterSensorDescription(
        entity_id="evse_today_energy",
        name="EVSE Today Energy",
        source="derived",
        calc="evse_today_energy",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
    ),

    "iotmeter_iet1": IoTMeterSensorDescription(
        entity_id="iotmeter_iet1",
        name="IoTmeter Total Import Energy L1",
        source="data",
        key="E1tP",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_iet2": IoTMeterSensorDescription(
        entity_id="iotmeter_iet2",
        name="IoTmeter Total Import Energy L2",
        source="data",
        key="E2tP",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_iet3": IoTMeterSensorDescription(
        entity_id="iotmeter_iet3",
        name="IoTmeter Total Import Energy L3",
        source="data",
        key="E3tP",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_iet": IoTMeterSensorDescription(
        entity_id="iotmeter_iet",
        name="IoTmeter Total Import Energy",
        source="derived",
        calc="sum_import_total",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
    ),

    "iotmeter_ee1": IoTMeterSensorDescription(
        entity_id="iotmeter_ee1",
        name="IoTmeter Today Export Energy L1",
        source="data",
        key="E1dN",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_ee2": IoTMeterSensorDescription(
        entity_id="iotmeter_ee2",
        name="IoTmeter Today Export Energy L2",
        source="data",
        key="E2dN",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_ee3": IoTMeterSensorDescription(
        entity_id="iotmeter_ee3",
        name="IoTmeter Today Export Energy L3",
        source="data",
        key="E3dN",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_ee": IoTMeterSensorDescription(
        entity_id="iotmeter_ee",
        name="IoTmeter Today Export Energy",
        source="derived",
        calc="sum_export_today",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
    ),
    "iotmeter_eep": IoTMeterSensorDescription(
        entity_id="iotmeter_eep",
        name="IoTmeter Yesterday Exported Energy",
        source="data",
        key="EpDN",
        device_class="energy",
        # Včerejší energie je denní výsledek, nikoli rostoucí čítač.
        # Bez state_class: běžná historie zůstává, nové dlouhodobé statistiky nevznikají.
        unit="kWh",
        transform="int_100_div",
    ),

    "iotmeter_eet1": IoTMeterSensorDescription(
        entity_id="iotmeter_eet1",
        name="IoTmeter Total Export Energy L1",
        source="data",
        key="E1tN",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_eet2": IoTMeterSensorDescription(
        entity_id="iotmeter_eet2",
        name="IoTmeter Total Export Energy L2",
        source="data",
        key="E2tN",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_eet3": IoTMeterSensorDescription(
        entity_id="iotmeter_eet3",
        name="IoTmeter Total Export Energy L3",
        source="data",
        key="E3tN",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        transform="int_100_div",
    ),
    "iotmeter_eet": IoTMeterSensorDescription(
        entity_id="iotmeter_eet",
        name="IoTmeter Total Export Energy",
        source="derived",
        calc="sum_export_total",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
    ),

    # ---------------------------------------------------------------------
    # CURRENTS I1–I3 (signed int16 / 100)
    # ---------------------------------------------------------------------
    "iotmeter_i1": IoTMeterSensorDescription(
        entity_id="iotmeter_i1",
        name="IoTmeter I1",
        source="data",
        key="I1",
        device_class="current",
        state_class="measurement",
        unit="A",
        transform="signed_16bit_100_div",
    ),
    "iotmeter_i2": IoTMeterSensorDescription(
        entity_id="iotmeter_i2",
        name="IoTmeter I2",
        source="data",
        key="I2",
        device_class="current",
        state_class="measurement",
        unit="A",
        transform="signed_16bit_100_div",
    ),
    "iotmeter_i3": IoTMeterSensorDescription(
        entity_id="iotmeter_i3",
        name="IoTmeter I3",
        source="data",
        key="I3",
        device_class="current",
        state_class="measurement",
        unit="A",
        transform="signed_16bit_100_div",
    ),

    # ---------------------------------------------------------------------
    # POWER P1–P3 (signed int16), P sum, EV Charger P
    # ---------------------------------------------------------------------
    "iotmeter_p1": IoTMeterSensorDescription(
        entity_id="iotmeter_p1",
        name="IoTmeter P1",
        source="data",
        key="P1",
        device_class="power",
        state_class="measurement",
        unit="W",
        transform="signed_16bit",
    ),
    "iotmeter_p2": IoTMeterSensorDescription(
        entity_id="iotmeter_p2",
        name="IoTmeter P2",
        source="data",
        key="P2",
        device_class="power",
        state_class="measurement",
        unit="W",
        transform="signed_16bit",
    ),
    "iotmeter_p3": IoTMeterSensorDescription(
        entity_id="iotmeter_p3",
        name="IoTmeter P3",
        source="data",
        key="P3",
        device_class="power",
        state_class="measurement",
        unit="W",
        transform="signed_16bit",
    ),
    "iotmeter_p_sum": IoTMeterSensorDescription(
        entity_id="iotmeter_p_sum",
        name="IoTmeter P",
        source="derived",
        calc="sum_p123",
        device_class="power",
        state_class="measurement",
        unit="W",
    ),
    "ev_charger_p": IoTMeterSensorDescription(
        entity_id="ev_charger_p",
        name="EV Charger P",
        source="derived",
        calc="ev_charger_p",
        device_class="power",
        state_class="measurement",
        unit="W",
    ),

    # ---------------------------------------------------------------------
    # Apparent power S1–S3 (signed int16)
    # ---------------------------------------------------------------------
    "iotmeter_s1": IoTMeterSensorDescription(
        entity_id="iotmeter_s1",
        name="IoTmeter S1",
        source="data",
        key="S1",
        device_class="apparent_power",
        state_class="measurement",
        unit="VA",
        transform="signed_16bit",
    ),
    "iotmeter_s2": IoTMeterSensorDescription(
        entity_id="iotmeter_s2",
        name="IoTmeter S2",
        source="data",
        key="S2",
        device_class="apparent_power",
        state_class="measurement",
        unit="VA",
        transform="signed_16bit",
    ),
    "iotmeter_s3": IoTMeterSensorDescription(
        entity_id="iotmeter_s3",
        name="IoTmeter S3",
        source="data",
        key="S3",
        device_class="apparent_power",
        state_class="measurement",
        unit="VA",
        transform="signed_16bit",
    ),
}


###############################################################################
#  BINARY SENSORS – HDO state, HDO charging
###############################################################################

BINARY_SENSOR_DEFINITIONS: dict[str, IoTMeterBinarySensorDescription] = {
    "iotmeter_hdo_state": IoTMeterBinarySensorDescription(
        entity_id="iotmeter_hdo_state",
        name="IoTmeter HDO State",
        source="derived",
        calc="hdo_state",
        device_class="power",
    ),
    "iotmeter_hdo_charging": IoTMeterBinarySensorDescription(
        entity_id="iotmeter_hdo_charging",
        name="IoTmeter HDO Charging",
        source="derived",
        calc="hdo_charging",
        device_class="power",
    ),
}
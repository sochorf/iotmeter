from __future__ import annotations

import logging
from typing import Any

import asyncio
import voluptuous as vol

from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_IP,
    DEFAULT_PORT,
    ENDPOINT_SETTINGS,
    VALID_DEVICE_ID,
)

_LOGGER = logging.getLogger(__name__)


async def _async_validate_iotmeter(
    hass: HomeAssistant,
    ip: str,
) -> dict[str, Any] | None:
    """Ověř dostupnost IoTMeteru – jednoduché HTTP volání."""
    url = f"http://{ip}:{DEFAULT_PORT}{ENDPOINT_SETTINGS}"

    session = async_get_clientsession(hass)
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status != 200:
                _LOGGER.warning("IoTMeter: HTTP %s z %s", resp.status, url)
                return None

            data = await resp.json(content_type=None)

    except (ClientError, asyncio.TimeoutError) as err:
        _LOGGER.error("IoTMeter: chyba komunikace s %s: %s", url, err)
        return None
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("IoTMeter: neočekávaná chyba: %s", err)
        return None

    # Ověříme ID zařízení (stejně jako v původních templátech – 93189 = OK)
    dev_id = str(data.get("ID", ""))
    if dev_id != VALID_DEVICE_ID:
        _LOGGER.warning(
            "IoTMeter: neočekávané ID zařízení '%s' (čekáno '%s')",
            dev_id,
            VALID_DEVICE_ID,
        )
        # necháme projít, jen varujeme – když chceš být přísný, vrať None

    return data


class IoTMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow pro IoTMeter."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """První krok – zadání IP adresy IoTMeteru."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ip = user_input[CONF_IP].strip()

            # Normalizace: odstranit http://, https:// a :port
            if ip.startswith("http://"):
                ip = ip[7:]
            elif ip.startswith("https://"):
                ip = ip[8:]
            if ":" in ip:
                ip = ip.split(":", 1)[0]

            # Zabránit duplicitním konfiguracím
            await self.async_set_unique_id(f"iotmeter_{ip}")
            self._abort_if_unique_id_configured()

            data = await _async_validate_iotmeter(self.hass, ip)
            if data is None:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"IoTMeter ({ip})",
                    data={CONF_IP: ip},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_IP): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Podpora YAML importu."""
        return await self.async_step_user(user_input)
"""Config flow for NEP Gateway Integration."""

from __future__ import annotations

from http import HTTPStatus
import logging
from typing import Any

import requests

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .core_exceptions import InvalidGatewayException

_LOGGER = logging.getLogger(__name__)

CONF_GATEWAY_URL = "gateway_url"
CONF_INVERTERS = "inverters"

RESULT_SUCCESS = 0
RESULT_FAIL = 1
RESULT_URL_FAIL = 2


class NEPGatewayFlowHandler(config_entries.ConfigFlow, DOMAIN):
    """Handle NEP Gateway config flow."""

    VERSION = 1
    MINOR_VERSION = 0
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize flow."""
        self._gateway_url: str | None = None
        self._inverters: list[str] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get Url for local connection, test it and save it."""

        # Probably should trim, etc.
        url = user_input[CONF_GATEWAY_URL]
        result = await self._check_connection(url)
        if result != RESULT_SUCCESS:
            return "error_connect"
        return self._save_config()

    async def _check_connection(self, url: str) -> int:
        """Attempt to access local NEP Gateway."""

        try:
            resp = requests.get(url, None, timeout=5)
            if resp.status_code not in (HTTPStatus.OK, HTTPStatus.ACCEPTED):
                _LOGGER.error("Error %s : %s", resp.status_code, resp.text)
                raise InvalidGatewayException
        except InvalidGatewayException as exc:
            msg = "Gateway url provided appears to not work."
            _LOGGER.exception(msg, exc_info=exc)
            return RESULT_URL_FAIL
        except Exception as exc:
            _LOGGER.exception("Error connecting to gateway.", exc_info=exc)
            return RESULT_FAIL

        return RESULT_SUCCESS

    @callback
    async def _save_config(self) -> FlowResult:
        """Save entry."""

        data = {CONF_GATEWAY_URL: self._gateway_url, CONF_INVERTERS: self._inverters}

        # if an entry exists, we are reconfiguring
        if entries := self._async_current_entries():
            entry = entries[0]
            self.hass.config_entries.async_update_entry(
                entry=entry,
                data=data,
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(entry.entry_id)
            )
            return self.async_abort(reason="reconfigured")

        return self.async_create_entry(title="NEP Inverters", data=data)

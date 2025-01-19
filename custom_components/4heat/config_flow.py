"""Config flows for our integration.

This config flow demonstrates many aspects of possible config flows.

Multi step flows
Menus
Using your api data in your flow
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_CODE, CONF_PASSWORD, CONF_PIN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import API, APIAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Adjust the data schema to the data that you need
# ----------------------------------------------------------------------------
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CODE, description={"suggested_value": ""}): str,
        vol.Required(CONF_PIN, description={"suggested_value": ""}): str,
        vol.Required(CONF_USERNAME, description={"suggested_value": ""}): str,
        vol.Required(CONF_PASSWORD, description={"suggested_value": ""}): str,
    }
)


def _raise_invalid_api_response(message):
    _LOGGER.error(message)
    raise InvalidAPIResponse(message)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        # ----------------------------------------------------------------------------
        # If your api is not async, use the executor to access it
        # If you cannot connect, raise CannotConnect
        # If the authentication is wrong, raise InvalidAuth
        # ----------------------------------------------------------------------------
        api = API(
            data[CONF_CODE], data[CONF_PIN], data[CONF_USERNAME], data[CONF_PASSWORD]
        )

        token = await api.get_token()
        file_map = await api.get_file_map(token)

        if file_map is None:
            _raise_invalid_api_response("No API response")

        if file_map.get("name") is None or len(file_map.get("name")) == 0:
            _raise_invalid_api_response("No device name returned")

    except InvalidAPIResponse as err:
        _LOGGER.error("Invalid API response")
        _LOGGER.error(err)
        raise InvalidAPIResponse from err
    except APIAuthError as err:
        _LOGGER.error("Error authenticating with 4Heat API")
        _LOGGER.error(err)
        raise InvalidAuth from err
    except Exception as err:
        _LOGGER.error("Error getting data from 4Heat API")
        _LOGGER.error(err)
        raise CannotConnect from err

    return file_map


class FourHeatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Example Integration."""

    VERSION = 1
    _input_data: dict[str, Any]
    _title: str

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step.

        Called when you initiate adding an integration via the UI
        """

        _LOGGER.info("Async_step_user")

        errors: dict[str, str] = {}

        if user_input is not None:
            # The form has been filled in and submitted, so process the data provided.
            try:
                file_map = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidAPIResponse:
                errors["base"] = "invalid_api_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                # Validation was successful, so create a unique id for this instance of your integration
                # and create the config entry.
                await self.async_set_unique_id(file_map.get("name"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=file_map["name"], data=user_input, options=file_map
                )

        # Show initial form.
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add reconfigure step to allow to reconfigure a config entry.

        This methid displays a reconfigure option in the integration and is
        different to options.
        It can be used to reconfigure any of the data submitted when first installed.
        This is optional and can be removed if you do not want to allow reconfiguration.
        """

        _LOGGER.info("Async_step_reconfigure")

        errors: dict[str, str] = {}
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            try:
                user_input[CONF_CODE] = config_entry.data[CONF_CODE]
                file_map = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidAPIResponse:
                errors["base"] = "invalid_api_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    config_entry,
                    unique_id=config_entry.unique_id,
                    data={**config_entry.data, **user_input},
                    options=file_map,
                    reason="reconfigure_successful",
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PIN, default=config_entry.data[CONF_PIN]): str,
                    vol.Required(
                        CONF_USERNAME, default=config_entry.data[CONF_USERNAME]
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidAPIResponse(HomeAssistantError):
    """Error to indicate there is an invalid api response."""

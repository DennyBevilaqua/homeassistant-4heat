"""DataUpdateCoordinator for 4Heat integration."""

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CODE, CONF_PASSWORD, CONF_PIN, CONF_USERNAME
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import API, APIAuthError, APIConnectionError
from .const import (
    DATA_IS_CONNECTED,
    DATA_LAST_TIMESTAMP,
    DATA_ROOM_TEMPERATURE,
    DATA_STATE,
    DATA_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


class FourHeatDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching 4heat data."""

    data: list[dict[str, Any]]

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.code = config_entry.data[CONF_CODE]
        self.pin = config_entry.data[CONF_PIN]
        self.user = config_entry.data[CONF_USERNAME]
        self.pwd = config_entry.data[CONF_PASSWORD]

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{HOMEASSISTANT_DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if you have made your
            # platform entities, CoordinatorEntities.
            # Using config option here but you can just use a fixed value.
            update_interval=timedelta(seconds=self.poll_interval),
        )

        # Initialise your api here and make available to your integration.
        self.api = API(code=self.code, pin=self.pin, user=self.user, pwd=self.pwd)
        self.token = None

    async def async_auth(self):
        """Authenticate with the API."""
        expires_in = datetime.strptime(
            self.token.get(".expires"), "%a, %d %b %Y %H:%M:%S %Z"
        )
        _LOGGER.info("Token expires in: %s", expires_in)

        if self.token is None or expires_in < datetime.now():
            self.token = await self.hass.async_add_executor_job(self.api.get_token)
            if self.token is None or not self.token.get("access_token"):
                raise APIAuthError("Authentication failed")

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to retrieve and pre-process the data into an appropriate data structure
        to be used to provide values for all your entities.
        """
        try:
            # ----------------------------------------------------------------------------
            # Get the data from your api
            # NOTE: Change this to use a real api call for data
            # ----------------------------------------------------------------------------
            await self.async_auth()
            r = await self.hass.async_add_executor_job(self.api.get_data, self.token)
            data = dict[str, Any]
            data[DATA_IS_CONNECTED] = r.get("IsConnected")
            data[DATA_LAST_TIMESTAMP] = r.get("LastTimestamp")

            values = r.get("LastMessageReceived").get("Values")
            state = None
            temperature = None
            room_temperature = None

            for value in values:
                if int(value.substr(0, 2), 16) == 16:
                    room_temperature = self.convertSignedValue(
                        int(hex.substr(6, 4), 16)
                    )
                    _LOGGER.info("Values: room_temperature: %s", room_temperature)

                    state = int(hex.substr(10, 2), 16)
                    _LOGGER.info("Values: state: %s", state)
                    errore = int(hex.substr(12, 2), 16)
                    _LOGGER.info("Values: errore: %s", errore)
                    temperature = self.convertSignedValue(int(hex.substr(20, 4), 16))
                    _LOGGER.info("Values: temperature: %s", temperature)

                    if value.length != 36:
                        pos_punto = int(hex.substr(36, 2), 16)
                        _LOGGER.info("Values: pos_punto: %s", pos_punto)

            data[DATA_STATE] = state
            data[DATA_TEMPERATURE] = temperature
            data[DATA_ROOM_TEMPERATURE] = room_temperature
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        return data

    async def async_set_temperature(self, temperature: float) -> bool:
        """Update data to API endpoint."""
        try:
            await self.async_auth()
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return True

    async def async_turn_off(self) -> bool:
        """Update data to API endpoint."""
        try:
            await self.async_auth()
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return True

    async def async_turn_on(self) -> bool:
        """Update data to API endpoint."""
        try:
            await self.async_auth()
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return True

    def convertSignedValue(self, value: int) -> int:
        """Convert a signed value to an integer."""
        if value > 32767:
            value = (65536 - value) * -1
        return value

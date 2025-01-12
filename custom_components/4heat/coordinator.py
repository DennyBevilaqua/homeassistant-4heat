"""DataUpdateCoordinator for 4Heat integration."""

from datetime import datetime, timedelta
import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CODE,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PIN,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import API, APIAuthError, APIConnectionError
from .const import (
    DATA_DEVICE_ERROR_CODE,
    DATA_DEVICE_ERROR_DESCRIPTION,
    DATA_DEVICE_IP,
    DATA_DEVICE_NAME,
    DATA_DEVICE_PORT,
    DATA_IS_CONNECTED,
    DATA_LAST_TIMESTAMP,
    DATA_ROOM_TEMPERATURE,
    DATA_SOFTWARE_VERSION,
    DATA_STATE,
    DATA_TARGET_TEMPERATURE,
    DEVICE_ERRORS,
    UPDATE_INTERVAL,
)
from .tcp import TCPCommunication, tcp_message_translation

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
        self.ip = config_entry.data.get(CONF_IP_ADDRESS, None)
        self.port = config_entry.data.get(CONF_PORT, 80)
        self.token = None
        self.com_type = "TCP"

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
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

        # Initialise your api here and make available to your integration.
        self.api = API(code=self.code, pin=self.pin, user=self.user, pwd=self.pwd)

        # Initialise your TCP Client
        self.tcp_client = TCPCommunication(self.ip, self.port)

    async def async_auth(self):
        """Authenticate with the API."""
        expires_in = datetime.strptime("2020-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

        if self.token is not None and self.token.get(".expires") is not None:
            expires_in = datetime.strptime(
                self.token.get(".expires"), "%a, %d %b %Y %H:%M:%S %Z"
            )

        if self.token is None or expires_in < datetime.now():
            self.token = await self.hass.async_add_executor_job(self.api.get_token)
            _LOGGER.error(
                "New Token Requested - old expires in: %s",
                expires_in.strftime("%Y-%m-%d %H:%M:%S"),
            )
            if self.token is None or not self.token.get("access_token"):
                raise APIAuthError("Authentication failed")

    async def async_update_data(self) -> dict[str, Any]:
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

            if self.ip != r.get("IpAddress"):
                self.ip = r.get("IpAddress")
                self.tcp_client = TCPCommunication(self.ip, self.port)

            data = {
                DATA_DEVICE_NAME: r.get("Name"),
                DATA_DEVICE_IP: self.ip,
                DATA_DEVICE_PORT: self.port,
                DATA_IS_CONNECTED: r.get("IsConnected"),
                DATA_LAST_TIMESTAMP: r.get("LastTimestamp"),
                DATA_SOFTWARE_VERSION: f"{r.get("ProductVersion")}.{r.get("FirmwareVersion")}.{r.get("FirmwareRevision")}",
            }

            values = []
            last_message: str = r.get("LastMessageReceived")

            if last_message is not None and len(last_message) > 0:
                message = json.loads(last_message)
                values = message.get("Values")

            state = None
            temperature = None
            room_temperature = None

            if self.com_type == "WS":
                for value in values:
                    if int(value[:2], 16) == 16:
                        state = int(value[10:12], 16)
                        error = int(value[12:14], 16)
                        room_temperature = self.__convertSignedValue(
                            int(value[20:24], 16)
                        )

                        # if len(value) > 36:
                        #    pos_punto = int(value[36:38], 16)
                    elif int(value[:2], 16) == 12 and value[2:4] == "81":
                        temperature = int(value[24:28], 16)

            resp = await self.tcp_client.read_data()

            if resp:
                dev_state = tcp_message_translation.get_device_state(resp)
                temperature = dev_state.target_temperature

            data[DATA_STATE] = "off" if int(state) == 0 else "on"
            data[DATA_TARGET_TEMPERATURE] = temperature
            data[DATA_ROOM_TEMPERATURE] = room_temperature
            data[DATA_DEVICE_ERROR_CODE] = error
            data[DATA_DEVICE_ERROR_DESCRIPTION] = DEVICE_ERRORS.get(
                str(error), "Unknown error"
            )

            _LOGGER.info("Data Loaded: %s", data)
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            _LOGGER.error(err, stack_info=True)
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        return data

    async def async_set_temperature(self, temperature: float) -> bool:
        """Update data to API endpoint."""
        try:
            await self.async_auth()
            _LOGGER.error("Setting temperature to %s", temperature)
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
            _LOGGER.error("Turning off")
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
            _LOGGER.error("Turning on")
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return True

    def __convertSignedValue(self, value: int) -> int:
        """Convert a signed value to an integer."""
        if value > 32767:
            value = (65536 - value) * -1
        return value

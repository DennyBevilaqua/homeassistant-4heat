"""DataUpdateCoordinator for 4Heat integration."""

import asyncio
from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CODE, CONF_PASSWORD, CONF_PIN, CONF_USERNAME
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import API, APIAuthError, APIConnectionError
from .const import UPDATE_INTERVAL
from .device import Device, device_loader
from .tcp import TCPCommunication, TCPCommunicationError

_LOGGER = logging.getLogger(__name__)


class FourHeatDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching 4heat data."""

    device: Device

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.code = config_entry.data[CONF_CODE]
        self.pin = config_entry.data[CONF_PIN]
        self.user = config_entry.data[CONF_USERNAME]
        self.pwd = config_entry.data[CONF_PASSWORD]
        self.file_map = config_entry.options
        self.token = None
        self.tcp_client = None
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

        device_loader.initiate(self.file_map)
        self.device = Device()

    async def __initiate_tcp(self):
        # Initialise TCP Client
        if self.tcp_client is None:
            if self.device.ip is None:
                await self.__update_from_cloud()
                if self.device.ip is None:
                    raise APIConnectionError("Not possible to get device IP Address")
            self.tcp_client = TCPCommunication(self.device.ip, self.device.port)

    async def async_auth(self):
        """Authenticate with the API."""
        expires_in = datetime.strptime("2020-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

        if self.token is not None and self.token.get(".expires") is not None:
            expires_in = datetime.strptime(
                self.token.get(".expires"), "%a, %d %b %Y %H:%M:%S %Z"
            )

        if self.token is None or expires_in < datetime.now():
            self.token = await self.api.get_token()

            if self.token is None or not self.token.get("access_token"):
                raise APIAuthError("Authentication failed")

    async def __update_from_cloud(self):
        await self.async_auth()
        resp = await self.api.get_data(self.token)
        device_loader.load_from_cloud(self.device, resp)

    async def __update_from_local(self):
        resp = await self.tcp_client.read_data()
        device_loader.load_from_local(self.device, resp)

    async def async_update_data(self) -> Device:
        """Fetch data from API endpoint.

        This is the place to retrieve and pre-process the data into an appropriate data structure
        to be used to provide values for all your entities.
        """
        try:
            # ----------------------------------------------------------------------------
            # Get the data from your api
            # NOTE: Change this to use a real api call for data
            # ----------------------------------------------------------------------------
            try:
                await self.__initiate_tcp()
                await self.__update_from_local()
            except TCPCommunicationError as e:
                _LOGGER.error(
                    "It was not possible to connect to 4Heat device(%s:%s)",
                    self.device.ip,
                    str(self.device.port),
                )
                _LOGGER.error(e)
                _LOGGER.warning("Will try to connect to cloud")
                await self.__update_from_cloud()

            _LOGGER.debug("Data Loaded: %s", self.device.to_dict())
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            _LOGGER.error(err, stack_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return self.device

    async def async_set_temperature(self, temperature: int) -> bool:
        """Set temperature."""
        resp = None
        try:
            try:
                await self.__initiate_tcp()
                resp = await self.tcp_client.set_temperature(self.device, temperature)
            except TCPCommunicationError as e:
                _LOGGER.error(e)

            if resp is None:
                _LOGGER.warning("Will try to send command via cloud")

                await self.async_auth()
                resp = await self.api.set_temperature(
                    self.device, self.token, temperature
                )

        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        await asyncio.sleep(10)

        return resp is not None

    async def async_turn_off(self) -> bool:
        """Turn the device off."""
        resp = None
        try:
            try:
                await self.__initiate_tcp()
                resp = await self.tcp_client.turn_off()
            except TCPCommunicationError as e:
                _LOGGER.error(e)

            if resp is None:
                _LOGGER.warning("Will try to send command via cloud")

                await self.async_auth()
                resp = await self.api.turn_off(self.token)

        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        await asyncio.sleep(10)

        return resp is not None

    async def async_turn_on(self) -> bool:
        """Turn the device on."""
        resp = None
        try:
            try:
                await self.__initiate_tcp()
                resp = await self.tcp_client.turn_on()
            except TCPCommunicationError as e:
                _LOGGER.error(e)

            if resp is None:
                _LOGGER.warning("Will try to send command via cloud")

                await self.async_auth()
                resp = await self.api.turn_on(self.token)

        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        await asyncio.sleep(10)

        return resp is not None

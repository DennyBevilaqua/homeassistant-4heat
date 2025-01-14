"""Test 4Heat TCP communication with 4Heat device."""

import asyncio
import logging

from api import API
from device import Device, device_loader
from tcp import TCPCommunication

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)
api = API("22022440", "1982", "denny@bevilaqua.eu", "DBcode3101!")
tcp_client = TCPCommunication("192.168.1.18", 80)
token = None


async def get_token():
    """Get token."""
    return await api.get_token()


async def power_off(client: TCPCommunication):
    """Send a power off command to the device."""
    _LOGGER.info("Initiate Power Off")
    response = await client.power_off()
    _LOGGER.info(response)
    _LOGGER.info("End Power Off")


async def power_on(client: TCPCommunication):
    """Send a power on command to the device."""
    _LOGGER.info("Initiate Power On")
    response = await client.power_off()
    _LOGGER.info(response)
    _LOGGER.info("End Power On")


async def local_set_temperature(device: Device, temperature: int = 21):
    """Send a set temperature command to the device."""
    _LOGGER.info("Initiate Set Temperature")
    response = await tcp_client.set_temperature(device, temperature)
    _LOGGER.debug(response)
    _LOGGER.info("End Set Temperature")


async def cloud_set_temperature(device: Device, temperature: int = 21):
    """Send a set temperature command to the device."""
    _LOGGER.info("Initiate Set Temperature")
    response = await api.set_temperature(device, token, temperature)
    _LOGGER.debug(response)
    _LOGGER.info("End Set Temperature")


async def local_read(device: Device) -> Device:
    """Test tcp read."""
    resp = await tcp_client.read_data()
    device_loader.load_from_local(device, resp)
    _LOGGER.info("Device Read: %s", device.to_dict())
    assert device.last_update is not None
    return device


async def cloud_read(device: Device) -> Device:
    """Test tcp read."""
    resp = await api.get_data(token)
    device_loader.load_from_cloud(device, resp)
    _LOGGER.info("Device Read: %s", device.to_dict())
    return device


# Run the test
async def test_local_read():
    """Test tcp read."""
    _LOGGER.debug("Result: %s", (await local_read(Device())).to_dict())


async def test_cloud_read() -> Device:
    """Test tcp read."""
    _LOGGER.debug("Result: %s", (await cloud_read(Device())).to_dict())


async def test_local_set_temperature(temperature: int):
    """Test local set temperature."""
    device = await local_read(Device())
    _LOGGER.debug("Initial status: %s", device.to_dict())
    await local_set_temperature(device, temperature)
    device = await local_read(Device())
    _LOGGER.debug("Final status: %s", device.to_dict())


async def test_cloud_set_temperature(temperature: int) -> Device:
    """Test cloud set temperature."""
    device = await cloud_read(Device())
    _LOGGER.debug("Initial status: %s", device.to_dict())
    await cloud_set_temperature(device, temperature)
    device = await cloud_read(Device())
    _LOGGER.debug("Final status: %s", device.to_dict())


token = asyncio.run(get_token())
asyncio.run(test_cloud_set_temperature(21))

"""Switch setup for our Integration."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import FourHeatBaseEntity
from .const import DOMAIN
from .coordinator import FourHeatDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Binary Sensors."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: FourHeatDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    # ----------------------------------------------------------------------------
    # Here we enumerate the switches in your data value from your
    # DataUpdateCoordinator and add an instance of your switch class to a list
    # for each one.
    # This maybe different in your specific case, depending on how your data is
    # structured
    # ----------------------------------------------------------------------------

    switches = [FourHeatSwitch(coordinator, "switch")]

    # Create the binary sensors.
    async_add_entities(switches)


class FourHeatSwitch(FourHeatBaseEntity, SwitchEntity):
    """Implementation of a switch.

    This inherits our FourHeatBaseEntity to set common properties.
    See base.py for this class.

    https://developers.home-assistant.io/docs/core/entity/switch
    """

    _attr_device_class = SwitchDeviceClass.SWITCH

    @property
    def is_on(self) -> bool | None:
        """Return if the binary sensor is on."""
        # This needs to enumerate to true or false
        return self.coordinator.device.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.async_turn_on()
        # ----------------------------------------------------------------------------
        # Use async_refresh on the DataUpdateCoordinator to perform immediate update.
        # Using self.async_update or self.coordinator.async_request_refresh may delay update due
        # to trying to batch requests.
        # ----------------------------------------------------------------------------
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.async_turn_off()
        # ----------------------------------------------------------------------------
        # Use async_refresh on the DataUpdateCoordinator to perform immediate update.
        # Using self.async_update or self.coordinator.async_request_refresh may delay update due
        # to trying to batch requests.
        # ----------------------------------------------------------------------------
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        attrs = {}
        attrs["is_connected"] = self.coordinator.device.is_connected
        attrs["state_code"] = self.coordinator.device.state
        attrs["state_desc"] = self.coordinator.device.state_description
        attrs["state_timestamp"] = self.coordinator.device.state_timestamp.isoformat()
        attrs["last_update"] = self.coordinator.device.last_update.isoformat()
        attrs["error_code"] = self.coordinator.device.error_code
        attrs["error"] = self.coordinator.device.error_description
        return attrs

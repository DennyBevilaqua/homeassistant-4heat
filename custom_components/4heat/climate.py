"""Climate platform for 4Heat devices."""

import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
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
    """Set up the Sensors."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: FourHeatDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    climates = [FourHeatClimate(coordinator, "lareira")]

    # Now create the climates.
    async_add_entities(climates)


class FourHeatClimate(FourHeatBaseEntity, ClimateEntity):
    """4Heat climate device."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1
    _attr_target_temperature_high = 45
    _attr_target_temperature_low = 15
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1

    def is_on(self) -> bool:
        """Return if the device is on."""
        return self.coordinator.device.is_on

    @property
    def hvac_mode(self):
        """Return new hvac mode - HEAT or OFF."""
        return HVACMode.HEAT if self.is_on() else HVACMode.OFF

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.device.room_temperature

    @property
    def target_temperature(self):
        """Return the current temperature."""
        return self.coordinator.device.target_temperature

    async def async_set_temperature(self, **kwargs):
        """Set target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            target_temperature = int(kwargs.get(ATTR_TEMPERATURE))

            resp = await self.coordinator.async_set_temperature(target_temperature)
            _LOGGER.debug("Response to set temperature command: %s", str(resp))
            await self.coordinator.async_refresh()
        else:
            _LOGGER.error("No temperature provided to set_temperature")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_turn_off()
        else:
            await self.coordinator.async_turn_on()

        await self.coordinator.async_refresh()

    async def async_toggle(self):
        """Toggle the entity."""
        if self.is_on():
            await self.async_turn_off()
        else:
            await self.async_turn_on()

        await self.coordinator.async_refresh()

    async def async_turn_on(self):
        """Turn the entity on."""
        if not self.is_on():
            await self.coordinator.async_turn_on()

    async def async_turn_off(self):
        """Turn the entity off."""
        if self.is_on():
            await self.coordinator.async_turn_off()

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        attrs = {}
        attrs["is_connected"] = self.coordinator.device.is_connected
        attrs["timestamp"] = self.coordinator.device.state_timestamp
        attrs["error_code"] = self.coordinator.device.error_code
        attrs["error"] = self.coordinator.device.error_description
        return attrs

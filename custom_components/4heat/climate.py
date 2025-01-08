"""Climate platform for 4Heat devices."""

import logging

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import FourHeatBaseEntity
from .const import DATA_STATE, DATA_TEMPERATURE, DOMAIN
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

    climates = [
        FourHeatClimate(coordinator, device, DATA_TEMPERATURE)
        for device in coordinator.data
        if device.get("device_type") == "SOCKET"
    ]

    # Now create the climates.
    async_add_entities(climates)


class FourHeatClimate(FourHeatBaseEntity, ClimateEntity):
    """4Heat climate device."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_hvac_mode = HVACMode.HEAT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1
    _attr_target_temperature_high = 45
    _attr_target_temperature_low = 15
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1

    async def async_set_temperature(
        self,
        temperature: float,
        hvac_mode: str,
        preset_mode: str,
        **kwargs,
    ) -> None:
        """Set new target temperature."""
        if self.coordinator.data[DATA_STATE] != "on":
            await self.coordinator.async_turn_on(self.device_id)

        await self.coordinator.async_set_temperature(self.device_id, temperature)
        await self.coordinator.async_refresh()

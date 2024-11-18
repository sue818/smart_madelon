from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import Platform
from .const import DOMAIN

from .fresh_air_controller import FreshAirSystem
import logging

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Madelon Ventilation component."""
    logging.getLogger(__name__).info("Setting up Madelon Ventilation")
    host = config[DOMAIN].get("host")
    system = FreshAirSystem(host)
    hass.data[DOMAIN] = {"system": system}
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Fresh Air System from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.FAN)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.SENSOR)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.SWITCH)
    )

    return True
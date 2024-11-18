from homeassistant.core import HomeAssistant
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

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up the Fresh Air System from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "fan")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "switch")
    )
    return True
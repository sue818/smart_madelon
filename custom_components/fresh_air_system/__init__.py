from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .fresh_air_controller import FreshAirSystem

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Madelon Ventilation component."""
    host = config[DOMAIN].get("host")
    system = FreshAirSystem(host)
    hass.data[DOMAIN] = {"system": system}
    return True

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Fresh Air System entities."""
    from .fan import async_setup_entry as setup_fan
    await setup_fan(hass, config_entry, async_add_entities)
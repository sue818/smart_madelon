from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .fresh_air_controller import FreshAirSystem

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Fresh Air System component."""
    # 从配置中获取主机地址
    host = config[DOMAIN].get("host")
    
    # 初始化 FreshAirSystem 实例
    system = FreshAirSystem(host)
    
    # 将实例存储在 hass.data 中
    hass.data[DOMAIN] = {"system": system}
    
    return True

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Fresh Air System entities."""
    from .fan import async_setup_entry as setup_fan
    await setup_fan(hass, config_entry, async_add_entities)
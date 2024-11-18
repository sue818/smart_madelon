from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from homeassistant.core import HomeAssistant, ConfigEntry, AddEntitiesCallback

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fresh Air System switch based on a config entry."""
    # 从 hass.data 中获取 FreshAirSystem 实例
    system = hass.data[DOMAIN][entry.entry_id]["system"]
    
    # 添加开关实体
    async_add_entities([FreshAirPowerSwitch(system)])

class FreshAirPowerSwitch(SwitchEntity):
    def __init__(self, system):
        self._attr_has_entity_name = True
        self._system = system
        self._attr_name = "Fresh Air Power"
        self._attr_unique_id = f"{DOMAIN}_power_switch_{system.id}"
        self._attr_is_on = system.is_power_on

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._system.id)},
            name="Fresh Air System",
            manufacturer="Madelon",
            model="Model XYZ",
            sw_version="1.0",
        )

    async def async_turn_on(self, **kwargs):
        self._system.turn_on()
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._system.turn_off()
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self):
        self._attr_is_on = self._system.is_power_on
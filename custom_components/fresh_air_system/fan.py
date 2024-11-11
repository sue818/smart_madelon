from homeassistant.components.fan import FanEntity
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Fresh Air System fan."""
    # 从 hass.data 中获取 FreshAirSystem 实例
    system = hass.data[DOMAIN]["system"]
    
    # 添加风扇实体
    async_add_entities([FreshAirFan(system)])

class FreshAirFan(FanEntity):
    def __init__(self, system):
        self._system = system
        self._attr_name = "Fresh Air Fan"
        self._attr_speed = system.supply_speed
        self._attr_is_on = system.power

    @property
    def speed_list(self):
        """Return the list of available speeds."""
        return ["off", "low", "medium", "high"]

    @property
    def is_on(self):
        """Return true if the fan is on."""
        return self._system.power

    @property
    def speed(self):
        """Return the current speed."""
        speed_map = {0: "off", 1: "low", 2: "medium", 3: "high"}
        return speed_map.get(self._system.supply_speed, "off")

    async def async_turn_on(self, speed=None, **kwargs):
        """Turn on the fan."""
        if not self._system.power:
            self._system.power = True
        if speed:
            await self.async_set_speed(speed)

    async def async_turn_off(self, **kwargs):
        """Turn off the fan."""
        self._system.power = False
        self._attr_speed = "off"
        self.async_write_ha_state()

    async def async_set_speed(self, speed):
        """Set the speed of the fan."""
        speed_map = {"off": 0, "low": 1, "medium": 2, "high": 3}
        speed_value = speed_map.get(speed, 0)

        if speed_value == 0:
            await self.async_turn_off()
        else:
            if not self._system.power:
                self._system.power = True
            self._system.supply_speed = speed_value
            self._attr_speed = speed
            self.async_write_ha_state() 
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Fresh Air System sensors."""
    # 从 hass.data 中获取 FreshAirSystem 实例
    system = hass.data[DOMAIN]["system"]
    
    # 添加传感器实体
    async_add_entities([
        FreshAirTemperatureSensor(system),
        FreshAirHumiditySensor(system)
    ])

class FreshAirTemperatureSensor(SensorEntity):
    def __init__(self, system):
        self._system = system
        self._attr_name = "Fresh Air Temperature"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_native_value = system.temperature

    async def async_update(self):
        self._attr_native_value = self._system.temperature

class FreshAirHumiditySensor(SensorEntity):
    def __init__(self, system):
        self._system = system
        self._attr_name = "Fresh Air Humidity"
        self._attr_native_unit_of_measurement = "%"
        self._attr_native_value = system.humidity

    async def async_update(self):
        self._attr_native_value = self._system.humidity
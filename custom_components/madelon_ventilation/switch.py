"""Switch platform for Madelon Ventilation."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_SW_VERSION,
)
from .fresh_air_controller import FreshAirSystem, OperationMode
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Madelon Ventilation switches."""
    system = hass.data[DOMAIN][entry.entry_id]["system"]
    
    # 首次读取所有寄存器数据到缓存
    _LOGGER.debug("Performing initial register read")
    success = await hass.async_add_executor_job(system._read_all_registers, True)
    _LOGGER.debug(f"Initial register read {'successful' if success else 'failed'}")
    
    if success:
        current_mode = system.mode
        _LOGGER.debug(f"Initial mode value: {current_mode}")
        
        # 创建开关并设置初始状态
        switches = [
            MadelonModeSwitch(system, "auto", OperationMode.AUTO, "Auto Mode"),
            MadelonModeSwitch(system, "manual", OperationMode.MANUAL, "Manual Mode"),
            MadelonModeSwitch(system, "timer", OperationMode.TIMER, "Timer Mode"),
            MadelonBypassSwitch(system),
        ]
        
        # 设置初始状态
        for switch in switches:
            if isinstance(switch, MadelonModeSwitch):
                # 简化模式匹配，不再检查 bypass 状态
                if current_mode == switch._operation_mode:
                    switch._is_on = True
            elif isinstance(switch, MadelonBypassSwitch):
                switch._is_on = system.bypass

    async_add_entities(switches)


class MadelonModeSwitch(SwitchEntity):
    """Representation of a Madelon Ventilation mode switch."""

    def __init__(self, system: FreshAirSystem, mode_id: str, operation_mode: OperationMode, name: str):
        """Initialize the switch."""
        self._system = system
        self._mode_id = mode_id
        self._operation_mode = operation_mode
        self._attr_name = name
        self._attr_unique_id = f"{system.unique_identifier}_mode_{mode_id}"
        self._attr_has_entity_name = True
        self._is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._system.unique_identifier)},
            name="Fresh Air System",
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            sw_version=DEVICE_SW_VERSION,
        )

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    def update(self) -> None:
        """Update the switch state."""
        try:
            current_mode = self._system.mode
            _LOGGER.debug(f"Switch {self._attr_name} got current_mode: {current_mode}")
            
            if current_mode is None:
                self._is_on = False
                return

            # 直接比较基本模式，不需要考虑 bypass
            self._is_on = (current_mode == self._operation_mode)
            
            _LOGGER.debug(
                f"Switch {self._attr_name} update complete: "
                f"current_mode={current_mode.value}, "
                f"operation_mode={self._operation_mode.value}, "
                f"is_on={self._is_on}"
            )
        except Exception as e:
            _LOGGER.error(f"Error updating switch {self._attr_name}: {e}")

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        try:
            # 直接设置基本模式，不需要考虑 bypass 状态
            _LOGGER.debug(f"Switch {self._attr_name} turning on: setting mode to {self._operation_mode.value}")
            
            register_address = self._system.REGISTERS['mode']
            register_value = self._system._convert_mode_string(self._operation_mode)
            
            if self._system.modbus.write_single_register(register_address, register_value):
                self._system._update_cache_value('mode', register_value)
                self.update()
                for sensor in self._system.sensors:
                    sensor.schedule_update_ha_state(True)
            else:
                _LOGGER.error(f"Failed to set mode to {self._operation_mode.value}")
                
        except Exception as e:
            _LOGGER.error(f"Error turning on switch {self._attr_name}: {e}")

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        try:
            if self._is_on:
                # 关闭时直接切换到 MANUAL 模式，不需要考虑 bypass 状态
                _LOGGER.debug(f"Switch {self._attr_name} turning off: setting mode to manual")
                
                register_address = self._system.REGISTERS['mode']
                register_value = self._system._convert_mode_string(OperationMode.MANUAL)
                
                if self._system.modbus.write_single_register(register_address, register_value):
                    self._system._update_cache_value('mode', register_value)
                    self.update()
                    for sensor in self._system.sensors:
                        sensor.schedule_update_ha_state(True)
                else:
                    _LOGGER.error("Failed to set mode to manual")
                
        except Exception as e:
            _LOGGER.error(f"Error turning off switch {self._attr_name}: {e}")


class MadelonBypassSwitch(SwitchEntity):
    """Representation of a Madelon Ventilation bypass switch."""

    def __init__(self, system: FreshAirSystem):
        """Initialize the bypass switch."""
        self._system = system
        self._attr_name = "Bypass"
        self._attr_unique_id = f"{system.unique_identifier}_bypass"
        self._attr_has_entity_name = True
        self._is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._system.unique_identifier)},
            name="Fresh Air System",
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            sw_version=DEVICE_SW_VERSION,
        )

    @property
    def is_on(self) -> bool:
        """Return true if bypass is on."""
        return self._is_on

    def update(self) -> None:
        """Update the bypass switch state."""
        try:
            # 直接从缓存中获取旁通状态
            bypass_state = self._system.bypass
            self._is_on = bool(bypass_state) if bypass_state is not None else False
            _LOGGER.debug(f"Bypass switch state updated: {self._is_on}")
        except Exception as e:
            _LOGGER.error(f"Error updating bypass switch state: {e}")
            self._is_on = False

    def turn_on(self, **kwargs):
        """Turn the bypass on."""
        try:
            # 直接写入旁通寄存器
            register_address = self._system.REGISTERS['bypass']
            if self._system.modbus.write_single_register(register_address, 1):
                self._system._update_cache_value('bypass', 1)
                self.update()
                # 通知其他相关实体更新状态
                for sensor in self._system.sensors:
                    sensor.schedule_update_ha_state(True)
            else:
                _LOGGER.error("Failed to turn on bypass")
        except Exception as e:
            _LOGGER.error(f"Error turning on bypass: {e}")

    def turn_off(self, **kwargs):
        """Turn the bypass off."""
        try:
            # 直接写入旁通寄存器
            register_address = self._system.REGISTERS['bypass']
            if self._system.modbus.write_single_register(register_address, 0):
                self._system._update_cache_value('bypass', 0)
                self.update()
                # 通知其他相关实体更新状态
                for sensor in self._system.sensors:
                    sensor.schedule_update_ha_state(True)
            else:
                _LOGGER.error("Failed to turn off bypass")
        except Exception as e:
            _LOGGER.error(f"Error turning off bypass: {e}")

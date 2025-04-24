from typing import Any, Optional, Dict, List, cast
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
# Helper function for percentage conversion
from homeassistant.util.percentage import ordered_list_item_to_percentage, percentage_to_ordered_list_item
from datetime import timedelta
from .const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_SW_VERSION,
)
from .fresh_air_controller import FreshAirSystem, OperationMode
import logging

ORDERED_NAMED_FAN_SPEEDS = ["low", "medium", "high"]  # off is not included


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Fresh Air System fan."""
    logging.getLogger(__name__).info("Setting up Fresh Air System fan")
    system = hass.data[DOMAIN][config_entry.entry_id]["system"]
    fan = FreshAirFan(config_entry, system)
    async_add_entities([fan])
    fan_S = FreshAirFan(config_entry, system)
    async_add_entities([fan_S])
    fan_E = FreshAirFan(config_entry, system)
    async_add_entities([fan_E])
    

    # Schedule regular updates
    async def async_update(now=None):
        """Update the entity."""
        try:
            # 使用 async_add_executor_job 运行同步的 update 方法
            await hass.async_add_executor_job(fan.update)
            # 确保实体已添加到 hass 并且状态有效
            if fan.hass and fan.available:
                fan.async_write_ha_state()
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating fan state: {e}", exc_info=True)
        try:
            # 使用 async_add_executor_job 运行同步的 update 方法
            await hass.async_add_executor_job(fan_S.update)
            # 确保实体已添加到 hass 并且状态有效
            if fan_S.hass and fan_S.available:
                fan_S.async_write_ha_state()
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating fan_S state: {e}", exc_info=True)
        try:
            # 使用 async_add_executor_job 运行同步的 update 方法
            await hass.async_add_executor_job(fan_E.update)
            # 确保实体已添加到 hass 并且状态有效
            if fan_E.hass and fan_E.available:
                fan_E.async_write_ha_state()
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating fan_E state: {e}", exc_info=True)    

    # 使用事件调度器设置定期更新
    async_track_time_interval(hass, async_update, timedelta(seconds=30))


class FreshAirFan(FanEntity):
    def __init__(self, entry: ConfigEntry, system: FreshAirSystem):
        super().__init__()
        self._system = system
        self._attr_has_entity_name = True
        self._attr_name = "Fan"
        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_unique_id = f"{DOMAIN}_fan_{system.unique_identifier}"
        # Remove preset modes to prevent them from showing in HomeKit
        self._attr_preset_modes = None
        self._attr_preset_mode = None

    # Properties
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
    def supported_features(self):
        """Flag supported features."""
        return (
            FanEntityFeature.SET_SPEED |
            FanEntityFeature.TURN_ON |
            FanEntityFeature.TURN_OFF
        )

    @property
    def is_on(self):
        """Return true if the fan is on."""
        return self._attr_is_on

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, self._system.supply_speed)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # 初始更新一次状态
        await self.hass.async_add_executor_job(self.update)

    def update(self):
        """Update the fan's state."""
        try:
            power = self._system.power
            speed = self._system.supply_speed

            self._attr_is_on = power if power is not None else False
            
            # Calculate percentage
            if not self._attr_is_on or speed is None:
                self._attr_percentage = 0
            else:
                try:
                    self._attr_percentage = ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, speed)
                except ValueError:
                    logging.getLogger(__name__).warning(f"Invalid speed value: {speed}")
                    self._attr_percentage = 0
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in fan update: {e}", exc_info=True)

    def turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan.

        Args:
            percentage: Optional speed percentage to set (0-100). If provided,
                       the fan will turn on at this speed.
            preset_mode: Optional preset mode to set. Not currently implemented.
            **kwargs: Additional arguments that might be supported in the future.

        Returns:
            None

        Note:
            If no percentage is provided, the fan will turn on at its last known speed.
        """
        if percentage is not None:
            self.set_percentage(percentage)
        else:
            self._system.power = True
        self.update()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off.

        Args:
            **kwargs: Additional arguments that might be supported in the future.

        Returns:
            None

        Note:
            This will completely stop the fan and set its state to off.
        """
        self._system.power = False
        self.update()

    def toggle(self, **kwargs: Any) -> None:
        """Toggle the fan."""
        if self._attr_is_on:
            self.turn_off(**kwargs)
        else:
            self.turn_on(**kwargs)

    def set_percentage(self, percentage: int):
        """Set the speed percentage of the fan."""
        if percentage == 0:
            self.turn_off()
            return

        self._system.power = True
        speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
        self._system.supply_speed = speed
        self._system.exhaust_speed = speed
        self.update()

    # Remove or comment out these preset-related methods
    # async def async_set_preset_mode(self, preset_mode: str) -> None:
    # def _convert_mode_to_preset(self, mode: OperationMode) -> str:
    # def _convert_preset_to_mode(self, preset: str) -> OperationMode:

class FreshAirFanSupply(FanEntity):
    def __init__(self, entry: ConfigEntry, system: FreshAirSystem):
        super().__init__()
        self._system = system
        self._attr_has_entity_name = True
        self._attr_name = "Fan"
        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_unique_id = f"{DOMAIN}_fanSupply_{system.unique_identifier}"
        # Remove preset modes to prevent them from showing in HomeKit
        self._attr_preset_modes = None
        self._attr_preset_mode = None

    # Properties
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
    def supported_features(self):
        """Flag supported features."""
        return (
            FanEntityFeature.SET_SPEED |
            FanEntityFeature.TURN_ON |
            FanEntityFeature.TURN_OFF
        )

    @property
    def is_on(self):
        """Return true if the fan is on."""
        return self._attr_is_on

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, self._system.supply_speed)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # 初始更新一次状态
        await self.hass.async_add_executor_job(self.update)

    def update(self):
        """Update the fan's state."""
        try:
            power = self._system.power
            speed = self._system.supply_speed

            self._attr_is_on = power if power is not None else False
            
            # Calculate percentage
            if not self._attr_is_on or speed is None:
                self._attr_percentage = 0
            else:
                try:
                    self._attr_percentage = ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, speed)
                except ValueError:
                    logging.getLogger(__name__).warning(f"Invalid speed value: {speed}")
                    self._attr_percentage = 0
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in fan update: {e}", exc_info=True)

    def turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan.

        Args:
            percentage: Optional speed percentage to set (0-100). If provided,
                       the fan will turn on at this speed.
            preset_mode: Optional preset mode to set. Not currently implemented.
            **kwargs: Additional arguments that might be supported in the future.

        Returns:
            None

        Note:
            If no percentage is provided, the fan will turn on at its last known speed.
        """
        if percentage is not None:
            self.set_percentage(percentage)
        else:
            self._system.power = True
        self.update()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off.

        Args:
            **kwargs: Additional arguments that might be supported in the future.

        Returns:
            None

        Note:
            This will completely stop the fan and set its state to off.
        """
        self._system.power = False
        self.update()

    def toggle(self, **kwargs: Any) -> None:
        """Toggle the fan."""
        if self._attr_is_on:
            self.turn_off(**kwargs)
        else:
            self.turn_on(**kwargs)

    def set_percentage(self, percentage: int):
        """Set the speed percentage of the fan."""
        if percentage == 0:
            self.turn_off()
            return

        self._system.power = True
        speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
        self._system.supply_speed = speed
        self.update()

    # Remove or comment out these preset-related methods
    # async def async_set_preset_mode(self, preset_mode: str) -> None:
    # def _convert_mode_to_preset(self, mode: OperationMode) -> str:
    # def _convert_preset_to_mode(self, preset: str) -> OperationMode:

class FreshAirFanExhaust(FanEntity):
    def __init__(self, entry: ConfigEntry, system: FreshAirSystem):
        super().__init__()
        self._system = system
        self._attr_has_entity_name = True
        self._attr_name = "Fan"
        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_unique_id = f"{DOMAIN}_fanExhaust_{system.unique_identifier}"
        # Remove preset modes to prevent them from showing in HomeKit
        self._attr_preset_modes = None
        self._attr_preset_mode = None

    # Properties
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
    def supported_features(self):
        """Flag supported features."""
        return (
            FanEntityFeature.SET_SPEED |
            FanEntityFeature.TURN_ON |
            FanEntityFeature.TURN_OFF
        )

    @property
    def is_on(self):
        """Return true if the fan is on."""
        return self._attr_is_on

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, self._system.exhaust_speed)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # 初始更新一次状态
        await self.hass.async_add_executor_job(self.update)

    def update(self):
        """Update the fan's state."""
        try:
            power = self._system.power
            speed = self._system.exhaust_speed

            self._attr_is_on = power if power is not None else False
            
            # Calculate percentage
            if not self._attr_is_on or speed is None:
                self._attr_percentage = 0
            else:
                try:
                    self._attr_percentage = ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, speed)
                except ValueError:
                    logging.getLogger(__name__).warning(f"Invalid speed value: {speed}")
                    self._attr_percentage = 0
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in fan update: {e}", exc_info=True)

    def turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan.

        Args:
            percentage: Optional speed percentage to set (0-100). If provided,
                       the fan will turn on at this speed.
            preset_mode: Optional preset mode to set. Not currently implemented.
            **kwargs: Additional arguments that might be supported in the future.

        Returns:
            None

        Note:
            If no percentage is provided, the fan will turn on at its last known speed.
        """
        if percentage is not None:
            self.set_percentage(percentage)
        else:
            self._system.power = True
        self.update()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off.

        Args:
            **kwargs: Additional arguments that might be supported in the future.

        Returns:
            None

        Note:
            This will completely stop the fan and set its state to off.
        """
        self._system.power = False
        self.update()

    def toggle(self, **kwargs: Any) -> None:
        """Toggle the fan."""
        if self._attr_is_on:
            self.turn_off(**kwargs)
        else:
            self.turn_on(**kwargs)

    def set_percentage(self, percentage: int):
        """Set the speed percentage of the fan."""
        if percentage == 0:
            self.turn_off()
            return

        self._system.power = True
        speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
        self._system.exhaust_speed = speed
        self.update()

    # Remove or comment out these preset-related methods
    # async def async_set_preset_mode(self, preset_mode: str) -> None:
    # def _convert_mode_to_preset(self, mode: OperationMode) -> str:
    # def _convert_preset_to_mode(self, preset: str) -> OperationMode:

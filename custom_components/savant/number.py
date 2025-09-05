"""Sensors for Savant Home Automation."""

import datetime

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    numbers: list[NumberEntity] = []
    coordinator = config.runtime_data
    if config.data["type"] == "Audio":
        numbers = (
            [Trim(coordinator, int(input_port)) for input_port in coordinator.inputs]
            + [
                Delay(coordinator, int(output), "left")
                for output in coordinator.outputs
            ]
            + [
                Delay(coordinator, int(output), "right")
                for output in coordinator.outputs
            ]
        )
    else:
        numbers = []

    async_add_entities(numbers)
    coordinator.numbers.extend(numbers)


class Trim(CoordinatorEntity, NumberEntity):
    """Trim control (configuration) for an input of a Savant audio matrix."""

    _attr_device_class = NumberDeviceClass.SOUND_PRESSURE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Trim"
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "dB"
    _attr_native_min_value = -10
    _attr_native_max_value = 10

    def __init__(self, coordinator, port):
        """Create a RawVolumeSensor setting the context to the port index."""
        super().__init__(coordinator, context=port)
        self.port = port

    @property
    def unique_id(self):
        """The unique id of the sensor - uses the savantID of the coordinator and the port index."""
        return f"{self.coordinator.info['savantID']}_input_{self.port}_trim"

    @property
    def device_info(self):
        """Links to the device defined by the media player."""
        return dr.DeviceInfo(
            identifiers={
                (DOMAIN, f"{self.coordinator.info['savantID']}.input{self.port}")
            },
            name=f"{self.coordinator.name} {self.coordinator.inputs[str(self.port)]}",
            via_device=(DOMAIN, self.coordinator.info["savantID"]),
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.api.set_input_property(self.port, "trim", int(value))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data
        if data is None:
            self._attr_available = False
        else:
            self._attr_available = True
            port_data = data["matrix"][self.port]
            self._attr_native_value = int(port_data["trim"])
        self.async_write_ha_state()


class Delay(CoordinatorEntity, NumberEntity):
    """Trim control (configuration) for an input of a Savant audio matrix."""

    _attr_device_class = NumberDeviceClass.DURATION
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ms"
    _attr_native_min_value = 0
    _attr_native_max_value = 85

    def __init__(self, coordinator, port, side):
        """Create a RawVolumeSensor setting the context to the port index."""
        super().__init__(coordinator, context=[port, side])
        self.port = port
        self.side = side
        self._attr_name = f"Delay {side}"

    @property
    def unique_id(self):
        """The unique id of the sensor - uses the savantID of the coordinator and the port index."""
        return f"{self.coordinator.info['savantID']}_{self.port}_{self.side}_delay"

    @property
    def device_info(self):
        """Links to the device defined by the media player."""
        return dr.DeviceInfo(
            identifiers={
                (DOMAIN, f"{self.coordinator.info['savantID']}.output{self.port}")
            },
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self.coordinator.api.set_input_property(
            self.port, f"delay-{self.side}", int(value)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data
        if data is None:
            self._attr_available = False
        else:
            self._attr_available = True
            port_data = data[self.port]
            self._attr_native_value = int(port_data["other"][f"delay{self.side}"])
        self.async_write_ha_state()

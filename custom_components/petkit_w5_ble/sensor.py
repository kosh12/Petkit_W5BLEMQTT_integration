from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка сенсоров."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    for device in coordinator.devices:
        sensors.extend([
            PetkitW5BatterySensor(coordinator, device),
            PetkitW5FoodLevelSensor(coordinator, device),
        ])
    
    async_add_entities(sensors)

class PetkitW5BatterySensor(CoordinatorEntity, SensorEntity):
    """Сенсор уровня батареи."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device['name']} Battery"
        self._attr_unique_id = f"{device['mac']}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_unit_of_measurement = "%"

    @property
    def state(self):
        """Возвращает состояние сенсора."""
        device_data = self.coordinator.data.get(self._device["mac"], {})
        return device_data.get("battery", 0)

class PetkitW5FoodLevelSensor(CoordinatorEntity, SensorEntity):
    """Сенсор уровня корма."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device['name']} Food Level"
        self._attr_unique_id = f"{device['mac']}_food_level"
        self._attr_unit_of_measurement = "%"

    @property
    def state(self):
        """Возвращает состояние сенсора."""
        device_data = self.coordinator.data.get(self._device["mac"], {})
        return device_data.get("food_level", 0)

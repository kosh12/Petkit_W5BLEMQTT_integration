from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка device tracker."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    trackers = []
    for device in coordinator.devices:
        trackers.append(PetkitW5DeviceTracker(coordinator, device))
    
    async_add_entities(trackers)

class PetkitW5DeviceTracker(CoordinatorEntity, ScannerEntity):
    """Device tracker для Petkit W5."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device['name']} Status"
        self._attr_unique_id = f"{device['mac']}_tracker"

    @property
    def source_type(self) -> SourceType:
        """Тип источника."""
        return SourceType.BLUETOOTH

    @property
    def is_connected(self):
        """Возвращает статус подключения."""
        device_data = self.coordinator.data.get(self._device["mac"], {})
        return device_data.get("status") == "online"

    @property
    def extra_state_attributes(self):
        """Дополнительные атрибуты."""
        device_data = self.coordinator.data.get(self._device["mac"], {})
        return {
            "battery_level": device_data.get("battery", 0),
            "food_level": device_data.get("food_level", 0),
            "last_updated": device_data.get("last_update")
        }

    @property
    def mac_address(self):
        """MAC адрес устройства."""
        return self._device["mac"]

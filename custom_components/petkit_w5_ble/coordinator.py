from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
import asyncio
import logging
from .petkit_device import PetkitW5Device

_LOGGER = logging.getLogger(__name__)

class PetkitW5Coordinator(DataUpdateCoordinator):
    """Координатор для обновления данных от устройств Petkit W5."""

    def __init__(self, hass, entry):
        """Инициализация координатора."""
        super().__init__(
            hass,
            _LOGGER,
            name="Petkit W5",
            update_interval=timedelta(seconds=60),
        )
        self.entry = entry
        self.devices = entry.data.get("devices", [])
        
        # Настройки подключения
        self.mqtt_config = {
            "broker": entry.data.get("mqtt_broker"),
            "port": entry.data.get("mqtt_port", 1883),
            "user": entry.data.get("mqtt_user", ""),
            "password": entry.data.get("mqtt_password", "")
        }
        
        self.petkit_devices = {}
        self._setup_devices()

    def _setup_devices(self):
        """Создание объектов устройств."""
        for device_config in self.devices:
            mac = device_config["mac"]
            mqtt_topic = device_config.get("mqtt_topic", f"petkit/w5/{mac.replace(':', '')}")
            
            device = PetkitW5Device(mac, self.mqtt_config)
            device.setup_mqtt(mqtt_topic)
            self.petkit_devices[mac] = device

    async def _async_update_data(self):
        """Обновление данных от устройств."""
        data = {}
        
        for device_config in self.devices:
            mac = device_config["mac"]
            device = self.petkit_devices[mac]
            
            try:
                # Попытка подключения
                if not device.is_connected:
                    await device.connect()
                
                # Получение данных
                if device.is_connected:
                    device_data = await device.get_status()
                    # Публикация в MQTT
                    device.publish_mqtt(device_data)
                else:
                    device_data = {"status": "offline"}
                
                data[mac] = device_data
                
            except Exception as e:
                _LOGGER.error(f"Ошибка обработки устройства {mac}: {e}")
                data[mac] = {"status": "error", "error": str(e)}
        
        return data

    async def feed_device(self, mac_address, amount=10):
        """Отправка команды кормления устройству."""
        if mac_address not in self.petkit_devices:
            _LOGGER.error(f"Устройство {mac_address} не найдено")
            return False

        device = self.petkit_devices[mac_address]
        
        try:
            # Попытка подключения, если нужно
            if not device.is_connected:
                connected = await device.connect()
                if not connected:
                    return False
            
            # Отправка команды кормления
            await device.feed_now(amount)
            
            # Обновление данных после кормления
            await self.async_request_refresh()
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Ошибка кормления устройства {mac_address}: {e}")
            return False

    async def async_shutdown(self):
        """Завершение работы координатора."""
        # Отключение всех устройств
        for device in self.petkit_devices.values():
            await device.disconnect()
        
        await super().async_shutdown()

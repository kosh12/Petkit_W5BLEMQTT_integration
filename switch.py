from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка переключателей."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    switches = []
    for device in coordinator.devices:
        switches.append(PetkitW5FeedSwitch(coordinator, device))
    
    async_add_entities(switches)

class PetkitW5FeedSwitch(CoordinatorEntity, SwitchEntity):
    """Переключатель для кормления."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device['name']} Feed Now"
        self._attr_unique_id = f"{device['mac']}_feed_switch"
        self._is_on = False

    @property
    def is_on(self):
        """Возвращает состояние переключателя."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Включение переключателя - кормление."""
        try:
            # Здесь будет вызов функции кормления
            success = await self._feed_device()
            if success:
                self._is_on = True
                self.async_write_ha_state()
                # Автоматически выключить через некоторое время
                await self._async_turn_off_later()
        except Exception as e:
            self.hass.logger.error(f"Ошибка кормления: {e}")

    async def async_turn_off(self, **kwargs):
        """Выключение переключателя."""
        self._is_on = False
        self.async_write_ha_state()

    async def _feed_device(self):
        """Отправка команды кормления устройству."""
        # Здесь будет реализация BLE/MQTT коммуникации
        # coordinator = self.coordinator
        # await coordinator.feed_device(self._device["mac"])
        return True

    async def _async_turn_off_later(self):
        """Автоматическое выключение через 2 секунды."""
        async def turn_off():
            await self.async_turn_off()
        
        self.hass.loop.call_later(2, lambda: self.hass.async_create_task(turn_off()))

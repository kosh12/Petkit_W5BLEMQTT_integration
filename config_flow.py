import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import homeassistant.helpers.config_validation as cv
from .const import (
    DOMAIN,
    CONF_DEVICES,
    CONF_MAC,
    CONF_NAME,
    CONF_MQTT_TOPIC,
    DEFAULT_NAME,
    DEFAULT_MQTT_TOPIC
)

class PetkitW5ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Конфигурационный flow для Petkit W5."""

    VERSION = 1

    def __init__(self):
        self.devices = []

    async def async_step_user(self, user_input=None):
        """Первый шаг конфигурации."""
        return await self.async_step_device()

    async def async_step_device(self, user_input=None):
        """Шаг добавления устройства."""
        errors = {}
        
        if user_input is not None:
            # Валидация MAC адреса
            mac = user_input[CONF_MAC]
            if not self._is_valid_mac(mac):
                errors[CONF_MAC] = "invalid_mac"
            
            if not errors:
                self.devices.append({
                    CONF_MAC: mac,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_MQTT_TOPIC: user_input[CONF_MQTT_TOPIC]
                })
                
                # Спросить, нужно ли добавить еще устройства
                return await self.async_step_add_another()
        
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Required(CONF_MAC): str,
            vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_MQTT_TOPIC): str,
        })
        
        return self.async_show_form(
            step_id="device",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_add_another(self, user_input=None):
        """Шаг вопроса о добавлении еще устройств."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_another",
                data_schema=vol.Schema({
                    vol.Required("add_another", default=False): bool,
                }),
            )
        
        if user_input["add_another"]:
            return await self.async_step_device()
        else:
            return self.async_create_entry(
                title="Petkit W5 BLE",
                data={CONF_DEVICES: self.devices},
            )

    def _is_valid_mac(self, mac):
        """Проверка валидности MAC адреса."""
        import re
        mac_pattern = re.compile(r'^([0-9A-F]{2}[:]){5}([0-9A-F]{2})$')
        return bool(mac_pattern.match(mac.upper()))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Получение options flow."""
        return PetkitW5OptionsFlowHandler(config_entry)

class PetkitW5OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow для Petkit W5."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Управление устройствами."""
        return await self.async_step_manage_devices()

    async def async_step_manage_devices(self, user_input=None):
        """Управление списком устройств."""
        # Здесь будет логика управления существующими устройствами
        devices = self.config_entry.data.get(CONF_DEVICES, [])
        
        return self.async_show_form(
            step_id="manage_devices",
            data_schema=vol.Schema({}),
        )

# config_flow.py
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from .const import (
    DOMAIN, CONF_DEVICES, CONF_MAC, CONF_NAME, CONF_MQTT_TOPIC,
    CONF_WIFI_SSID, CONF_WIFI_PASSWORD, CONF_MQTT_BROKER,
    CONF_MQTT_PORT, CONF_MQTT_USER, CONF_MQTT_PASSWORD,
    DEFAULT_NAME, DEFAULT_MQTT_TOPIC
)

class PetkitW5ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Конфигурационный flow для Petkit W5."""

    VERSION = 1

    def __init__(self):
        self.config_data = {}
        self.devices = []

    async def async_step_user(self, user_input=None):
        """Первый шаг - настройки подключения."""
        return await self.async_step_connection()

    async def async_step_connection(self, user_input=None):
        """Шаг настройки подключения (WiFi и MQTT)."""
        errors = {}
        
        if user_input is not None:
            self.config_data.update({
                CONF_WIFI_SSID: user_input[CONF_WIFI_SSID],
                CONF_WIFI_PASSWORD: user_input[CONF_WIFI_PASSWORD],
                CONF_MQTT_BROKER: user_input[CONF_MQTT_BROKER],
                CONF_MQTT_PORT: user_input[CONF_MQTT_PORT],
                CONF_MQTT_USER: user_input[CONF_MQTT_USER],
                CONF_MQTT_PASSWORD: user_input[CONF_MQTT_PASSWORD],
            })
            return await self.async_step_device()
        
        data_schema = vol.Schema({
            vol.Required(CONF_WIFI_SSID): str,
            vol.Required(CONF_WIFI_PASSWORD): str,
            vol.Required(CONF_MQTT_BROKER): str,
            vol.Required(CONF_MQTT_PORT, default=1883): int,
            vol.Optional(CONF_MQTT_USER, default=""): str,
            vol.Optional(CONF_MQTT_PASSWORD, default=""): str,
        })
        
        return self.async_show_form(
            step_id="connection",
            data_schema=data_schema,
            errors=errors,
        )

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
                    CONF_MAC: mac.upper(),
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
            # Объединяем все данные
            self.config_data[CONF_DEVICES] = self.devices
            return self.async_create_entry(
                title="Petkit W5 BLE",
                data=self.config_data,
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
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_device", "manage_devices"]
        )

    async def async_step_add_device(self, user_input=None):
        """Добавление нового устройства."""
        errors = {}
        
        if user_input is not None:
            mac = user_input[CONF_MAC]
            if not self._is_valid_mac(mac):
                errors[CONF_MAC] = "invalid_mac"
            
            if not errors:
                # Добавляем устройство к существующим
                devices = self.config_entry.data.get(CONF_DEVICES, []).copy()
                devices.append({
                    CONF_MAC: mac.upper(),
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_MQTT_TOPIC: user_input[CONF_MQTT_TOPIC]
                })
                
                # Обновляем конфигурацию
                new_data = dict(self.config_entry.data)
                new_data[CONF_DEVICES] = devices
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                
                return self.async_create_entry(title="", data={})
        
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Required(CONF_MAC): str,
            vol.Required(CONF_MQTT_TOPIC, default=DEFAULT_MQTT_TOPIC): str,
        })
        
        return self.async_show_form(
            step_id="add_device",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_manage_devices(self, user_input=None):
        """Управление существующими устройствами."""
        # Здесь можно реализовать удаление/редактирование устройств
        return self.async_create_entry(title="", data={})

    def _is_valid_mac(self, mac):
        """Проверка валидности MAC адреса."""
        import re
        mac_pattern = re.compile(r'^([0-9A-F]{2}[:]){5}([0-9A-F]{2})$')
        return bool(mac_pattern.match(mac.upper()))

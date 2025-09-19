import struct
import asyncio
import logging
from bleak import BleakClient
import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

class PetkitW5Device:
    """Класс для работы с устройством Petkit W5 через BLE и MQTT."""
    
    # BLE UUIDs
    DEVICE_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
    DEVICE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
    FEED_CHAR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
    BLE_CHAR_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
    SETTING_CHAR_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

    def __init__(self, mac_address, mqtt_config=None):
        self.mac_address = mac_address
        self.client = None
        self.is_connected = False
        self.mqtt_client = None
        self.mqtt_config = mqtt_config
        self.last_data = {}

    async def connect(self):
        """Подключение к устройству через BLE."""
        try:
            self.client = BleakClient(self.mac_address)
            await self.client.connect()
            self.is_connected = await self.client.is_connected()
            _LOGGER.info(f"Подключение к {self.mac_address}: {'Успешно' if self.is_connected else 'Не удалось'}")
            return self.is_connected
        except Exception as e:
            _LOGGER.error(f"Ошибка подключения к {self.mac_address}: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Отключение от устройства."""
        if self.client and self.is_connected:
            try:
                await self.client.disconnect()
                self.is_connected = False
                _LOGGER.info(f"Отключение от {self.mac_address}")
            except Exception as e:
                _LOGGER.error(f"Ошибка отключения от {self.mac_address}: {e}")

    def checksum(self, data):
        """Вычисление контрольной суммы."""
        return sum(data) & 0xFF

    async def send_command(self, char_uuid, cmd):
        """Отправка команды устройству."""
        if not self.is_connected or not self.client:
            raise Exception("Устройство не подключено")

        try:
            await self.client.write_gatt_char(char_uuid, cmd)
            _LOGGER.debug(f"Команда отправлена: {cmd.hex()}")
        except Exception as e:
            _LOGGER.error(f"Ошибка отправки команды: {e}")
            raise

    async def feed_now(self, amount=10):
        """Команда кормления."""
        cmd = bytearray([0x01, 0x02, amount, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        cmd[12] = self.checksum(cmd)
        await self.send_command(self.FEED_CHAR_UUID, cmd)
        _LOGGER.info(f"Команда кормления отправлена: {amount} грамм")

    async def get_status(self):
        """Получение статуса устройства."""
        if not self.is_connected:
            return {"status": "offline"}

        try:
            # Здесь должна быть реализация получения реальных данных
            # Пока используем заглушку с реалистичными данными
            data = {
                "status": "online",
                "battery": 95,
                "food_level": 80,
                "last_update": asyncio.get_event_loop().time()
            }
            self.last_data = data
            return data
        except Exception as e:
            _LOGGER.error(f"Ошибка получения статуса: {e}")
            return {"status": "error", "error": str(e)}

    def setup_mqtt(self, topic):
        """Настройка MQTT клиента."""
        if not self.mqtt_config:
            return

        try:
            self.mqtt_client = mqtt.Client()
            if self.mqtt_config.get("user") and self.mqtt_config.get("password"):
                self.mqtt_client.username_pw_set(
                    self.mqtt_config["user"], 
                    self.mqtt_config["password"]
                )
            
            self.mqtt_client.connect(
                self.mqtt_config["broker"],
                self.mqtt_config["port"],
                60
            )
            self.mqtt_topic = topic
            _LOGGER.info(f"MQTT клиент настроен для топика: {topic}")
        except Exception as e:
            _LOGGER.error(f"Ошибка настройки MQTT: {e}")

    def publish_mqtt(self, data):
        """Публикация данных в MQTT."""
        if not self.mqtt_client or not hasattr(self, 'mqtt_topic'):
            return

        try:
            import json
            payload = json.dumps(data)
            self.mqtt_client.publish(f"{self.mqtt_topic}/status", payload)
            _LOGGER.debug(f"Данные опубликованы в MQTT: {payload}")
        except Exception as e:
            _LOGGER.error(f"Ошибка публикации в MQTT: {e}")

    def on_mqtt_message(self, client, userdata, msg):
        """Обработка входящих MQTT сообщений."""
        try:
            import json
            payload = json.loads(msg.payload.decode())
            _LOGGER.debug(f"Получено MQTT сообщение: {payload}")
            
            # Обработка команд из MQTT
            if "feed" in payload:
                amount = payload.get("feed", 10)
                # Здесь должна быть асинхронная отправка команды
                # asyncio.create_task(self.feed_now(amount))
                
        except Exception as e:
            _LOGGER.error(f"Ошибка обработки MQTT сообщения: {e}")

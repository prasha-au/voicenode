import asyncio
import logging
from typing import Optional, Callable, Awaitable, Dict, Set
import aiomqtt
import os

class MqttConnection:
  _instance: Optional['MqttConnection'] = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def __init__(self) -> None:
    self._hostname = os.getenv('MQTT_HOST', '192.168.1.4')
    self._port = int(os.getenv('MQTT_PORT', '1883'))
    self.client: Optional[aiomqtt.Client] = None
    self._reconnect_task: Optional[asyncio.Task] = None
    self._message_handlers: Dict[str, Set[Callable[[aiomqtt.Message], Awaitable[None]]]] = {}
    self._subscriptions: Set[str] = set()
    self._is_connected: bool = False

  async def connect(self) -> None:
    self.client = aiomqtt.Client(hostname=self._hostname, port=self._port, keepalive=5)
    if self._reconnect_task:
      return
    self._reconnect_task = asyncio.create_task(self._reconnect_loop())

  async def _reconnect_loop(self) -> None:
    while True:
      try:
        async with self.client:
          self._is_connected = True
          for topic in self._subscriptions:
            await self.client.subscribe(topic)
          logging.info("MQTT connected.")
          async for message in self.client.messages:
            await self._handle_message(message)
      except aiomqtt.MqttError as e:
        self._is_connected = False
        logging.warning(f"MQTT connection lost; Reconnecting in 5 seconds... {e}")
        await asyncio.sleep(5)

  async def _handle_message(self, message: aiomqtt.Message) -> None:
    topic = str(message.topic)
    if topic in self._message_handlers:
      for handler in self._message_handlers[topic]:
        try:
          await handler(message)
        except Exception as e:
          logging.error(f"Error in message handler for {topic}: {e}")

  def register_handler(self, topic: str, handler: Callable[[aiomqtt.Message], Awaitable[None]]) -> None:
    if topic not in self._message_handlers:
      self._message_handlers[topic] = set()
    self._message_handlers[topic].add(handler)

  def unregister_handler(self, topic: str, handler: Callable[[aiomqtt.Message], Awaitable[None]]) -> None:
    if topic in self._message_handlers:
      self._message_handlers[topic].discard(handler)
      if not self._message_handlers[topic]:
        del self._message_handlers[topic]

  async def subscribe(self, topic: str) -> None:
    self._subscriptions.add(topic)
    if self._is_connected:
      await self.client.subscribe(topic)

  async def unsubscribe(self, topic: str) -> None:
    self._subscriptions.discard(topic)
    if self._is_connected:
      await self.client.unsubscribe(topic)

  async def publish(self, topic: str, payload: str, retain: bool = False) -> None:
    if not self._is_connected:
      raise RuntimeError('MQTT not connected')
    await self.client.publish(topic, payload, retain=retain)

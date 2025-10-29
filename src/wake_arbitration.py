import asyncio
import time
import json
import logging
import socket
from typing import Optional
import aiomqtt
from mqtt import MqttConnection

ARBITRATION_WINDOW = 0.3
ARBITRATION_TIMEOUT = 5.0
DEVICE_ID = socket.gethostname()

class WakeArbitration:
  def __init__(self, mqtt: MqttConnection) -> None:
    self._mqtt = mqtt
    self._latest_trigger: Optional[dict] = None

  async def connect(self) -> None:
    await self._mqtt.subscribe("voicenode/wake")
    self._mqtt.register_handler("voicenode/wake", self._handle_wake_message)

  async def _handle_wake_message(self, message: aiomqtt.Message) -> None:
    if not message.payload:
      return
    self._latest_trigger = json.loads(message.payload.decode())

  async def should_handle_request(self, confidence: float) -> bool:
    score = int(round(confidence * 1000))
    logging.info(f'Arbitrating with score {score}')

    print(self._latest_trigger)

    if self._latest_trigger and self._latest_trigger['deviceId'] != DEVICE_ID:
      trigger_age = time.time() - self._latest_trigger['timestamp']
      if trigger_age < ARBITRATION_WINDOW:
        if score <= self._latest_trigger['score']:
          logging.info(f'Lost arbitration to {self._latest_trigger}')
          return False
      elif trigger_age < ARBITRATION_TIMEOUT:
        logging.info(f'Another device already handling request: {self._latest_trigger}')
        return False

    await self._mqtt.publish("voicenode/wake", json.dumps({
      'deviceId': DEVICE_ID,
      'score': score,
      'timestamp': int(time.time())
    }), retain=True)

    await asyncio.sleep(ARBITRATION_WINDOW + 0.1)

    return self._latest_trigger['deviceId'] == DEVICE_ID

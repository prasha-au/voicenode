import asyncio
import json
import uuid
import base64
from typing import Optional, Dict, Any, AsyncIterator, TypedDict
import aiomqtt
from mqtt import MqttConnection

class RequestPayload(TypedDict):
  pattern: str
  data: Dict[str, Any]
  id: str


class ResponsePayloadData(TypedDict):
  type: str
  data: str


class ResponsePayload(TypedDict):
  id: str
  data: ResponsePayloadData


class Homenode:
  def __init__(self, mqtt: MqttConnection):
    self._mqtt = mqtt
    self._session_id: Optional[str] = None
    self._event_queue: asyncio.Queue[ResponsePayloadData] = asyncio.Queue()

  async def connect(self) -> None:
    await self._mqtt.subscribe('aidev/chat/reply')
    self._mqtt.register_handler('aidev/chat/reply', self._handle_message)

  async def _handle_message(self, message: aiomqtt.Message) -> None:
    if not self._session_id:
      return
    response_topic = f'ai/live/{self._session_id}/response'
    if str(message.topic) == response_topic:
      try:
        payload: ResponsePayload = json.loads(message.payload.decode())
        response_data = payload.get('data')
        if response_data:
          await self._event_queue.put(response_data)
      except (json.JSONDecodeError, KeyError):
        pass

  async def _send_request(self, topic: str, data: Dict[str, Any]) -> None:
    request_payload: RequestPayload = {
      'pattern': topic,
      'data': data,
      'id': str(uuid.uuid4())
    }
    await self._mqtt.publish(topic, json.dumps(request_payload))

  async def wait_for_open(self) -> None:
    while True:
      event = await self._event_queue.get()
      if event['type'] == 'open':
        return


  async def start_session(self) -> None:
    if self._session_id:
      raise RuntimeError('Session is already active')

    self._session_id = f'live_{str(uuid.uuid4())}'
    await self._send_request('ai/live/startSession', {'sessionId': self._session_id})

    response_topic = f'ai/live/{self._session_id}/response'
    self._mqtt.register_handler(response_topic, self._handle_session_message)
    await self._mqtt.subscribe(response_topic)

    await asyncio.wait_for(self.wait_for_open(), timeout=5.0)


  async def end_session(self) -> None:
    response_topic = f'ai/live/{self._session_id}/response'
    await self._mqtt.unsubscribe(response_topic)
    self._mqtt.unregister_handler(response_topic, self._handle_session_message)
    self._session_id = None

  async def _handle_session_message(self, message: aiomqtt.Message) -> None:
    try:
      payload: ResponsePayload = json.loads(message.payload.decode())
      response_data = payload.get('data')
      if response_data:
        await self._event_queue.put(response_data)
    except (json.JSONDecodeError, KeyError):
      pass


  async def send_audio(self, audio_data: bytes) -> None:
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    await self._send_request('ai/live/request', {
      'sessionId': self._session_id,
      'audioBase64': audio_base64,
      'mimeType': 'audio/pcm;rate=16000'
    })

  async def get_events_stream(self) -> AsyncIterator[ResponsePayloadData]:
    while True:
      try:
        event = await self._event_queue.get()
        yield event
      except asyncio.CancelledError:
        break

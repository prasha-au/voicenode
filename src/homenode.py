import asyncio
import json
import uuid
import base64
from typing import Optional, Dict, Any, AsyncIterator, TypedDict
import aiomqtt


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
  def __init__(self):
    self.client: Optional[aiomqtt.Client] = None
    self._session_id: str = 'live_invalid'
    self._event_queue: asyncio.Queue[ResponsePayloadData] = asyncio.Queue()
    self._listening_task: Optional[asyncio.Task] = None

  async def connect(self) -> None:
    if self.client:
      return

    self.client = aiomqtt.Client(hostname='192.168.1.4', port=1883)
    await self.client.__aenter__()
    await self.client.subscribe('aidev/chat/reply')

  async def _send_request(self, topic: str, data: Dict[str, Any]) -> None:
    request_payload: RequestPayload = {
      'pattern': topic,
      'data': data,
      'id': str(uuid.uuid4())
    }
    await self.client.publish(topic, json.dumps(request_payload))

  async def _message_listener(self) -> None:
    response_topic = f'ai/live/{self._session_id}/response'

    await self.client.subscribe(response_topic)
    async for message in self.client.messages:
      if str(message.topic) == response_topic:
        try:
          payload: ResponsePayload = json.loads(message.payload.decode())
          response_data = payload.get('data')
          if response_data:
            await self._event_queue.put(response_data)
        except (json.JSONDecodeError, KeyError):
          continue


  async def wait_for_open(self) -> None:
    while True:
      event = await self._event_queue.get()
      if event['type'] == 'open':
        return


  async def start_session(self) -> None:
    if self._listening_task:
      raise RuntimeError('Session is already active')

    self._session_id = f'live_{str(uuid.uuid4())}'
    await self._send_request('ai/live/startSession', {'sessionId': self._session_id})
    self._listening_task = asyncio.create_task(self._message_listener())
    await asyncio.wait_for(self.wait_for_open(), timeout=5.0)


  async def end_session(self) -> None:
    if self._listening_task:
      self._listening_task.cancel()
      try:
        await self._listening_task
      except asyncio.CancelledError:
        pass
      self._listening_task = None


  async def send_audio(self, audio_data: bytes) -> None:
    if not self.client:
      raise RuntimeError('Homenode not connected')

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

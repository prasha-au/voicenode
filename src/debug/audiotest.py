
import pyaudio
import wave
import time

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
FRAME_SIZE = 512

def record_raw_audio(duration=16, filename='testraw.wav'):
  pa = pyaudio.PyAudio()
  stream = pa.open(format=pyaudio.paInt16, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=FRAME_SIZE)
  frames = []

  print('recording')
  start_time = time.time()
  while time.time() - start_time < duration:
    data = stream.read(FRAME_SIZE, exception_on_overflow=False)
    frames.append(data)

  print('done recording')
  stream.stop_stream()
  stream.close()
  pa.terminate()

  with wave.open(filename, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(SAMPLE_WIDTH)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))

  print(f'Recording raw saved to {filename}')


record_raw_audio()


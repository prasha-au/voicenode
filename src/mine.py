import pyaudio
import numpy as np
from openwakeword.model import Model
import time

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280
audio = pyaudio.PyAudio()

owwModel = Model(wakeword_models=['/home/prasha/voicenode/Hola_casita.tflite'], inference_framework='tflite')


def callback(in_data, frame_count, time_info, status):
    data = np.fromstring(in_data, dtype=np.int16)

    all_predictions = owwModel.predict(data)

    prediction = list(all_predictions.values())[0]

    if prediction > 0.5:
      print(prediction)
    else:
      print('.')

    return (in_data, pyaudio.paContinue)


# Notice the extra stream callback...
stream = audio.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

stream.start_stream()

# The loop is different as well...
while stream.is_active():
    time.sleep(0.1)

# Exit with ctrl+C"
# This still doesn't run.

stream.stop_stream()
stream.close()
p.terminate()




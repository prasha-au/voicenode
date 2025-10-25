from scipy.io import wavfile
import numpy as np
from speexdsp import EchoCanceller

FRAME_SIZE = 4096
SAMPLE_RATE = 16000

rate, data = wavfile.read('testraw.wav')
far_rate, far_end_data = wavfile.read('../talking_noise.wav')

# Ensure far_end_data is same length as data
if len(far_end_data) < len(data):
    far_end_data = np.pad(far_end_data, (0, len(data) - len(far_end_data)), 'constant')
else:
    far_end_data = far_end_data[:len(data)]

# Create AEC
# 4096 = 256ms filter
aec = EchoCanceller.create(FRAME_SIZE, 4096, SAMPLE_RATE)

processed = b''
for i in range(0, len(data), FRAME_SIZE):
    frame = data[i:i + FRAME_SIZE]
    far_frame = far_end_data[i:i + FRAME_SIZE]

    # Pad if necessary
    if len(frame) < FRAME_SIZE:
        frame = np.pad(frame, (0, FRAME_SIZE - len(frame)), 'constant')
        far_frame = np.pad(far_frame, (0, FRAME_SIZE - len(far_frame)), 'constant')

    frame_bytes = frame.astype(np.int16).tobytes()
    far_bytes = far_frame.astype(np.int16).tobytes()

    out_bytes = aec.process(frame_bytes, far_bytes)
    processed += out_bytes

# Trim to original length
processed_array = np.frombuffer(processed, dtype=np.int16)[:len(data)]

# Save processed audio
wavfile.write('testaec.wav', rate, processed_array)
print('Saved testaec.wav')
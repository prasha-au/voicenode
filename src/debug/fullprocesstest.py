from scipy.io import wavfile
import numpy as np
import sys
sys.path.insert(0, '..')
from audioprocessor import AudioProcessor

FRAME_SIZE = 4096
SAMPLE_RATE = 16000

rate, data = wavfile.read('testraw.wav')
far_rate, far_end_data = wavfile.read('../talking_noise.wav')

# Ensure far_end_data is same length as data
if len(far_end_data) < len(data):
    far_end_data = np.pad(far_end_data, (0, len(data) - len(far_end_data)), 'constant')
else:
    far_end_data = far_end_data[:len(data)]

# Create processor
processor = AudioProcessor(frame_size=FRAME_SIZE, sample_rate=SAMPLE_RATE)

# Process audio in 1024-byte chunks (simulating real-time callback)
CALLBACK_SIZE = 1024
print('starting')
for i in range(0, len(data), CALLBACK_SIZE):
    mic_chunk = data[i:i + CALLBACK_SIZE]
    far_chunk = far_end_data[i:i + CALLBACK_SIZE]

    # Pad if necessary
    if len(mic_chunk) < CALLBACK_SIZE:
        mic_chunk = np.pad(mic_chunk, (0, CALLBACK_SIZE - len(mic_chunk)), 'constant')
        far_chunk = np.pad(far_chunk, (0, CALLBACK_SIZE - len(far_chunk)), 'constant')

    mic_bytes = mic_chunk.astype(np.int16).tobytes()
    far_bytes = far_chunk.astype(np.int16).tobytes()

    # Submit to processor
    processor.submit(mic_bytes, far_bytes)

# Collect all processed output
processed = b''
while True:
    result = processor.get_processed()
    if result is None:
        break
    processed += result

# Convert to array
processed_array = np.frombuffer(processed, dtype=np.int16)

# Save processed audio
wavfile.write('test_fullprocess.wav', rate, processed_array)
print(f'Saved test_fullprocess.wav ({len(processed_array)} samples)')
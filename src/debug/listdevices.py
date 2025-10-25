import pyaudio


# Create a PyAudio object
p = pyaudio.PyAudio()

# Get the number of available audio devices
num_devices = p.get_device_count()

print("Available Audio Devices:")
# Iterate through each device and print its name
for i in range(num_devices):
    device_info = p.get_device_info_by_index(i)
    device_name = device_info.get('name')
    print(f"Device ID: {i}, Name: {device_name}")

# Terminate the PyAudio object
p.terminate()
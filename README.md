# Voice Node
This contains a satellite voice assistant node for my [Homenode](https://prasha.au/projects/homenode) home automation system. A lot of the AI features are contained within that system so this node just handles wake word detection, audio processing, and streaming audio to/from the server.

This project aims for **cheap** hardware. You will most likely get better performance designing with an XMOS hardware based system but you should be able to splatter more of these around the house and hopefully make use of any software improvements in the future.

## Hardware
- Raspberry Pi 3+
- [Respeaker 2-Mics Pi HAT](https://www.aliexpress.com/item/32902300949.html) (using v1)
- [4Ω speaker (up to 5W)](https://www.aliexpress.com/item/1005005699690954.html)
- [3D printed case](./voicenode.3mf)


## Audio Pipeline
The audio processing is challenging with the Gemini Live API as any speaker feedback will interrupt the model's output.

### 1. Dynamic Capture Volume Control
The system dynamically adjusts microphone capture volume in sync with audio playback. When the speaker is active, capture volume is reduced minimizing the amount of speaker output picked up by the microphone This adjustment occurs before any acoustic echo cancellation (AEC) or noise reduction (NR) is applied. While hacky, this has a big impact and work well my usage of the device as I will usually I will speak louder to cancel or correct an action.

### 2. Acoustic Echo Cancellation (AEC)
Acoustic Echo Cancellation (AEC) is implemented using SpeexDSP. This needs to be aligned to your audio pipeline latency but is the most effective way to remove speaker echo from the mic input.

### 3. Noise Reduction
Non-stationary spectral gating via [noisereduce](https://github.com/timsainb/noisereduce) is used to remove residual echo and background noise. These parameters should be adjusted to optimize performance on your setup. You may be able to run [RNNoise](https://github.com/pengzhendong/pyrnnoise) on a Pi4+ but I was not able to keep up with input.



# Imager

We base this off a standard Raspbian Bookworm Lite image. Use the Rpi Imager to setup credentials, etc.
From there we run `setup.sh` after it boots with a network to install drivers + docker. Finally we can just push prebuilt containers running in privileged mode.

```
docker build --platform=linux/arm64 -t voicenode .
```

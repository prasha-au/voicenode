#!/bin/bash

set +e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )


sudo cp "${SCRIPT_DIR}/config.txt" /boot/firmware/config.txt

cd /tmp
wget https://github.com/HinTak/seeed-voicecard/archive/refs/heads/v6.12.zip -O voicecard-drivers.zip
unzip voicecard-drivers.zip
cd seeed-voicecard-6.12
sudo ./install.sh


curl -sSL https://get.docker.com | sh
sudo usermod -aG docker voicenode


touch "${SCRIPT_DIR}/completed"
sudo reboot

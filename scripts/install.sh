#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Ruotolo Vincenzo. All rights reserved.
#
# This software is proprietary and licensed, not sold. See the LICENSE.md file
# in the project root for the full license terms.
#
# Unauthorized copying, distribution, modification, or resale of this file,
# via any medium, is strictly prohibited without prior written permission.
# -----------------------------------------------------------------------------
set -euo pipefail

TARGET_PLATFORM=$1

#! Dependencies
echo "Installing host packages for RP2040 build on Debian/Ubuntu..."
sudo apt update
sudo apt install -y git make cmake build-essential pkg-config \
    gcc gcc-arm-none-eabi g++ libnewlib-arm-none-eabi binutils-arm-none-eabi ca-certificates \
    python3 python3-pip python3-venv \
    wget curl unzip libusb-1.0-0-dev

# optional but highly useful
sudo apt install -y ninja-build openocd gdb-multiarch \
    python3-setuptools python3-wheel

# serial utilities & basic utils
sudo apt install -y minicom screen rsync

# for pyocd (alternative flasher)
pip3 install --user pyocd --break-system-packages

# python YAML lib used by build scripts
pip3 install --user pyyaml --break-system-packages
python3 -m pip install --user click --break-system-packages

#! udev / permissions
# add user to dialout (serial) group
sudo apt install usbutils
sudo usermod -aG dialout $USER


#! rp2040
if [[ $TARGET_PLATFORM == "rp2040" ]]; then
    echo "RP2040 install toolchain"

    # from your repo root (or anywhere)
    cd third_party

    git clone https://github.com/raspberrypi/pico-sdk.git
    git submodule update --init --recursive

    # set env (bash)
    export PICO_TOOLCHAIN_PATH=/usr/bin
    export PICO_SDK_PATH=$PWD/pico-sdk

    cd ..

#! esp32
elif [[ $TARGET_PLATFORM == "esp32" ]]; then
    echo "ESP32 install toolchain"

    python3 -m pip install --user -U platformio --break-system-packages

#! stm32
elif [[ $TARGET_PLATFORM == "stm32" ]]; then
    echo "STM32 install toolchain"

#! default
else
    echo "No target found"

fi

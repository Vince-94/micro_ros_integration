#!/bin/bash
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Ruotolo Vincenzo. All rights reserved.
#
# This software is proprietary and licensed, not sold. See the LICENSE.md file
# in the project root for the full license terms.
#
# Unauthorized copying, distribution, modification, or resale of this file,
# via any medium, is strictly prohibited without prior written permission.
# -----------------------------------------------------------------------------

# Colors
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
GREEN="\033[1;32m"
MAGENTA="\033[1;35m"
BLUE="\033[1;34m"
WHITE="\033[1;37m"
NC="\033[0m" # No Color

echo -en "${RED}"
echo "##############################"
echo "# micro-ROS integration Tool #"
echo "##############################"
echo -en "${NC}"

CURRENT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")


#! Prechecks
# Cheks OS
if [ ! "$(uname)" == "Linux" ]; then
    echo "Unsupported OS"
    exit 1
fi


#! install
if [[ $1 == "install" ]]; then
    # arg1 = target platform (e.g., rp2040, esp32, stm32)
    ./scripts/install.sh $2


#! build
elif [[ $1 == "build" ]]; then
    # arg1 = target platform (e.g., rp2040, esp32, stm32)
    python3 scripts/build.py --platform $2


#! flash
elif [[ $1 == "flash" ]]; then
    python3 scripts/flash.py --platform $2 --wait 2


#! verify
elif [[ $1 == "verify" ]]; then
    python3 scripts/verify.py --platform $2 --no-agent


#! clean
elif [[ $1 == "clean" ]]; then
    rm -rf platforms/$2/build


#! help
elif [[ $1 == "help" ]]; then
    echo -en "${CYAN}"
    echo "Help"
    echo -en "\n${YELLOW}"


#! default
else
    echo "Default"

fi

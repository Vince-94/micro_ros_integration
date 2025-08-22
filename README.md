# micro-ROS Integration

- [micro-ROS Integration](#micro-ros-integration)
  - [Overview](#overview)
  - [Requirements](#requirements)
  - [How to use](#how-to-use)
  - [CI](#ci)
  - [Credits \& Acknowledgements](#credits--acknowledgements)
    - [Project contributors](#project-contributors)
    - [License \& third-party licenses](#license--third-party-licenses)
    - [Reporting omissions or suggesting credits](#reporting-omissions-or-suggesting-credits)
  - [Roadmap](#roadmap)


## Overview

This project is intended to be a ready-to-run micro-ROS integration kit in order to setup a micro-ROS supported microcontroller with micro-ROS. The processes provided are:
1. install dependencies
2. build firmware
3. flash firmware
4. verify firmware build and flash
5. clean artifacts for a new build

In such way, the user should be able to plug microcontrollers into an existing ROS2 system via micro-ROS (Micro XRCE-DDS) using either UART, UDP (Wi-Fi), or a custom transport.


## Requirements

- Python 3.8 or greater
- Host platform:
  - `Linux`: full support
  - `Windows`: with WSL2, limited in simulation and GUI
  - `macOS`: experimental
- Target platform (MCU)
  - `rp2040`
  - `esp32`
  - `stm32`
- Transport layer:
  - `uart`
  - `udp`
  - `serial`


## How to use

1. Install deps
    ```sh
    source cli.sh install <PLATFORM>
    ```
2. Build firmware
    ```sh
    source cli.sh build <PLATFORM>
    ```
3. Flash firmware
    ```sh
    source cli.sh flash <PLATFORM> [METHOD]
    ```

> [!NOTE]
> Refer to [cheatsheet](docs/cheatsheet.md) for all the available commands.


## CI

Provide a sample GitHub Actions workflow that runs a cross-compile (no hardware), runs static analysis, and builds a firmware artifact.

Optional hardware-in-the-loop (HIL) job can be configured to flash a test device connected to the CI runner (self-hosted runner required).


## Credits & Acknowledgements

Thank you to the many projects, communities and people that make this toolkit possible. This project builds on a large ecosystem of open-source software — please consult the licenses of the individual projects for full terms.

### Project contributors
- **Ruotolo Vincenzo** — project author, primary maintainer.
- Thanks to early testers and colleagues who provided feedback, bug reports and real-world test cases.

### License & third-party licenses
This project is distributed under the license in `LICENSE.md` at the project root. Third-party components used by this project are governed by their own licenses (Debian/Ubuntu packages, ROS packages, Python packages, Docker images). **Before redistributing derived images or binaries**, please review upstream license terms and comply with their requirements.

### Reporting omissions or suggesting credits
If we missed a library, contributor, or other project that should be acknowledged, please open an issue or send a pull request — we will add it promptly.


## Roadmap
- [ ] Supported OS
  - [ ] MacOS
- [ ] CI

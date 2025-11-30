# Cheatsheet

- [Cheatsheet](#cheatsheet)
  - [CLI commands](#cli-commands)
  - [Target MCU](#target-mcu)
    - [RP2040](#rp2040)
    - [RP2350](#rp2350)
    - [STM32](#stm32)
    - [ESP32](#esp32)


## CLI commands

```sh
source cli.sh <CMD> <SUB_CMD>
```

| **CMD** | **SUB_CMD**        | **Description**                     |
| ------- | ------------------ | ----------------------------------- |
| install | [PLATFORM]         | Install dependencies                |
| build   | [PLATFORM]         | Build firmware for target PLATFORM  |
| flash   | [PLATFORM] [LAYER] | Flash firmware for target PLATFORM  |
| verify  | [PLATFORM]         | Verify firmware for target PLATFORM |
| clean   | [PLATFORM]         | Clean artifacts for target PLATFORM |

SUB_CMD:
- `PLATFORM`: rp2040, esp32, stm32
- `LAYER`: uart, udp, serial


## Target MCU

### RP2040


### RP2350


### STM32


### ESP32


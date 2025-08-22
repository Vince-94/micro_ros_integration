// platforms/rp2040/adapter.c
#include "platform_adapter.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/timer.h"


// Example UART transport (stub). Adjust to your actual micro-ROS transport.
#define UART_TX_PIN 0
#define UART_RX_PIN 1


int platform_init(void) {
    stdio_init_all();
    gpio_init(UART_TX_PIN);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_init(UART_RX_PIN);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
    // Additional initialization for micro-ROS transport (UART, USB, etc.)
    return 0;
}


int platform_transport_open(void) {
// Stub: ensure UART/USB transport is ready
    return 0;
}


int platform_transport_write(const uint8_t *buf, size_t len) {
// Replace with UART/USB write implementation
    for (size_t i = 0; i < len; i++) {
        putchar_raw(buf[i]);
    }
    return (int)len;
}


int platform_transport_read(uint8_t *buf, size_t len) {
    // Stub: blocking read; replace with non-blocking or interrupt-driven if desired
    size_t i = 0;
    while (i < len) {
        int c = getchar_timeout_us(1000);
        if (c == PICO_ERROR_TIMEOUT) {
            break;
        } else {
            buf[i++] = (uint8_t)c;
        }
    }
    return (int)i;
}


void platform_delay_ms(uint32_t ms) {
    sleep_ms(ms);
}
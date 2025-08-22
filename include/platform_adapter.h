#ifndef PLATFORM_ADAPTER_H
#define PLATFORM_ADAPTER_H


#include <stdint.h>   // for uint8_t, uint32_t, uint64_t
#include <stddef.h>   // for size_t


#ifdef __cplusplus
extern "C" {
#endif


// called early to init clocks/peripherals
int platform_init(void);

// time helpers
uint64_t platform_millis(void);
void platform_delay_ms(uint32_t ms);

// transport: send/recv bytes for the XRCE transport (if using custom transport)
int platform_transport_write(const uint8_t *buf, size_t len);
int platform_transport_read(uint8_t *buf, size_t maxlen);

int platform_transport_open(void);
void platform_transport_close(void);

// reset / watchdog helpers
void platform_system_reset(void);


#ifdef __cplusplus
}
#endif
#endif
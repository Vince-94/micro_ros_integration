#ifndef PLATFORM_ADAPTER_H
#define PLATFORM_ADAPTER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Low-level board init (clocks, GPIOs, etc.)
int platform_init(void);

// Time helpers
uint64_t platform_millis(void);
void platform_delay_ms(uint32_t ms);

// Transport: simple blocking write/read for XRCE bytes
// Return number of bytes written/read, or negative on error
int platform_transport_write(const uint8_t *buf, size_t len);
int platform_transport_read(uint8_t *buf, size_t maxlen);

// Helper: enable/disable interrupts (optional)
void platform_disable_interrupts(void);
void platform_enable_interrupts(void);

// Soft reset if available
void platform_system_reset(void);

#ifdef __cplusplus
}
#endif

#endif // PLATFORM_ADAPTER_H
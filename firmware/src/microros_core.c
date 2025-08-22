#include <stdio.h>
#include "platform_adapter.h"
#include <string.h>

// Replace this with actual micro-ROS client initialization and main loop.
// Typical steps when integrating micro-ROS XRCE client:
//  - Initialize micro-ROS transport using platform_transport_write / read
//  - Initialize rcl/rclc and create nodes/publishers/subscribers
//  - Spin/loop the executor and process micro-ROS client cycle
// See your micro-ROS client documentation for required initialization APIs.

void microros_entrypoint(void) {
    // Example: placeholder behavior to demonstrate transport
    // The real micro-ROS client should call platform_transport_* to send/receive XRCE frames.
    const char *msg = "Hello from Pico (no micro-ROS linked)\r\n";
    for (int i = 0; i < 5; ++i) {
        platform_transport_write((const uint8_t*)msg, strlen(msg));
        platform_delay_ms(1000);
    }
}
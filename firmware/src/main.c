#include "platform_adapter.h"
#include <stdio.h>


int main(void) {
    platform_init();

    if (platform_transport_open() != 0) {
        printf("Transport open failed!\n");
        return -1;
    }


    printf("micro-ROS firmware started.\n");


    // Minimal main loop stub (replace with rclc_executor in micro-ROS integration)
    while (1) {
        // Example: echo received bytes back
        uint8_t buf[32];
        int n = platform_transport_read(buf, sizeof(buf));
        if (n > 0) {
            platform_transport_write(buf, (size_t)n);
        }
        platform_delay_ms(10);
    }


    return 0;
}
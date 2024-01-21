#include <stdio.h>
#include <string.h>
#include <exception>

// Pico
#include "pico/stdlib.h"

#include "config.h" // compile time configuration options
#include "adc_dma.hpp"

void my_gpio_init(void) {
    // LED pin init
    gpio_init(LED1_PIN);
    gpio_set_dir(LED1_PIN, GPIO_OUT);
    gpio_put(LED1_PIN, 0);
}

void actual_main(void) {
    my_gpio_init();
    my_adc_init();

    // init STDIO
    stdio_init_all();
    stdio_uart_init_full(uart0, 115200, 4, -1);

    puts("Hello");

    // TODO
    //  - get continuous read to work properly
    //  - set up HPF
    //  - set up trigger mechanism
    //  - See what we get
    bool led_state = true;
    while (1) {
        // puts("*");
        adc_queue.debug();
        if(not adc_queue.is_empty()) {
            led_state = not led_state;
            gpio_put(LED1_PIN, led_state);
            uint16_t *data = adc_queue.pop();

            uint32_t sum = 0;
            for(uint i=0; i<ADC_BLOCK_SIZE; ++i) {
                sum += data[i]&0xFFF;
            }

            float adc = (float) sum * 3.3 / (1<<12) / ADC_BLOCK_SIZE;
            float tempC = 27.0f - (adc - 0.706f) / 0.001721f;
            printf("%.2f C\n", tempC);

            delete [] data;
        }

        // main loop blink
        // gpio_put(LED1_PIN, (time_us_32() % 1000000) < 100000);
    }
}

int main(void) {
    try {
        actual_main();
    } catch (const std::exception &e) {
        puts("Exception occured:");
        puts(e.what());
    } catch (...) {
        puts("Unknown exception occured");
    }

    while(1) {
        gpio_put(LED1_PIN, (time_us_32() % 200000) < 100000);
    }
}

#include <stdio.h>
#include <string.h>
#include <exception>

// Pico
#include "pico/stdlib.h"

#include "version.h"
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
    // stdio_uart_init_full(uart0, 115200, 4, -1);

    puts("BetaBoard");
    puts(GIT_COMMIT_HASH);
    puts(COMPILE_DATE);

    // TODO
    //  - get continuous read to work properly
    //  - set up HPF
    //  - set up trigger mechanism
    //  - See what we get
    bool led_state = true;
    uint32_t last_print = time_us_32();
    while (1) {
        if((time_us_32() - last_print) > 1e6) {
            // puts("*");
            adc_queue.debug();
            last_print = time_us_32();
        }
        if(not adc_queue.is_empty()) {
            // led_state = not led_state;
            // gpio_put(LED1_PIN, led_state);
            uint16_t *data = adc_queue.pop();

            /*
            for(uint i=0; i<ADC_BLOCK_SIZE; i+=8) {
                printf("%03X %03X %03X %03X %03X %03X %03X %03X ", data[i]&0xFFF, data[i+1]&0xFFF, data[i+2]&0xFFF, data[i+3]&0xFFF, data[i+4]&0xFFF, data[i+5]&0xFFF, data[i+6]&0xFFF, data[i+7]&0xFFF);
            }
            puts("");
            */

            uint32_t sum = 0;
            uint16_t min=0xFFFF, max=0;
            for(uint i=0; i<ADC_BLOCK_SIZE; ++i) {
                uint16_t sample = data[i]&0xFFF;
                sum += sample;
                if(sample < min)
                    min = sample;
                if(sample > max)
                    max = sample;
            }

            float adc = (float) sum * 3.3 / (1<<12) / ADC_BLOCK_SIZE;
            printf("%.3f V, min=%.3f V, max=%.3f V\n", adc, min*3.3/(1<<12), max*3.3/(1<<12));
            // float tempC = 27.0f - (adc - 0.706f) / 0.001721f;
            // printf("%.2f C\n", tempC);

            delete [] data; // NOTE: Keep me!!
        }

        // main loop blink
        gpio_put(LED1_PIN, (time_us_32() % 1000000) < 900000);
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

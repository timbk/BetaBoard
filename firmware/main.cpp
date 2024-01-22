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

void print_timeseries_info(int16_t *data) {
    int32_t sum = 0;
    int16_t min=0x7FFF, max=-0x7FFF;
    for(uint i=0; i<ADC_BLOCK_SIZE; ++i) {
        int16_t sample = data[i];
        sum += sample;
        if(sample < min)
            min = sample;
        if(sample > max)
            max = sample;
    }

    float adc = (float) sum * 3.3 / (1<<12) / ADC_BLOCK_SIZE;
    float min_v = (min*3.3/(float)(1<<12));
    float max_v = (max*3.3/(float)(1<<12));
    // printf("min_v %.3f V\n", min_v);
    if((min_v < -0.055) or (max_v > 0.055)) {
        printf("%.3f V, min=%.3f V, max=%.3f V %c\n", adc, min*3.3/(1<<12), max*3.3/(1<<12), abs(min)>max ? '-': '+');
    }
    // float tempC = 27.0f - (adc - 0.706f) / 0.001721f;
    // printf("%.2f C\n", tempC);
}

void print_peaks(int16_t *data) {
    const int16_t threshold = -0.055 * (float)(1<<12) / 3.3;
    uint start, stop;
    const uint pre=64, post=64, ignore=64;

    for(uint i=0; i<ADC_BLOCK_SIZE; ++i) {
        if(data[i] < threshold) {
            start = (i >= pre) ? i-pre : 0;
            stop = (i <= (ADC_BLOCK_SIZE-post)) ? i+post : ADC_BLOCK_SIZE;
            for(uint j=start; j<stop; ++j) {
                printf("%i ", data[j]);
            }
            puts("");

            i += ignore;
        }
    }
}

void lpf(int16_t *array, uint len) {
    // minimalistic impelemntation of a 1 element sos HPF (HPF means a2=b2=0)
    static const float a1=-0.96906742, b0=0.98453371, b1=-0.98453371;

    static float last_value = 0;
    float current_value;

    for(uint i=0; i<len; ++i) {
        current_value = array[i] - a1*last_value;
        float tmp = current_value*b0 + last_value*b1;
        // printf("%u %.3f\n", array[i], tmp);
        array[i] = tmp; 
        last_value = current_value;
    }
}

void actual_main(void) {
    my_gpio_init();

    // init STDIO
    stdio_init_all();
    // stdio_uart_init_full(uart0, 115200, 4, -1);

    puts("BetaBoard");
    puts(GIT_COMMIT_HASH);
    puts(COMPILE_DATE);

    puts("ADC init..");
    my_adc_init();
    puts("ADC init done");


    // TODO
    //  - get continuous read to work properly
    //  - set up HPF
    //  - set up trigger mechanism
    //  - See what we get
    bool led_state = true;
    uint32_t last_print = time_us_32();
    uint32_t block_cnt = 0;
    while (1) {
        if((time_us_32() - last_print) > 10e6) {
            // puts("*");
            // adc_queue.debug();
            last_print = time_us_32();
            printf("block_cnt: %lu\n", block_cnt);
        }
        if(not adc_queue.is_empty()) {
            int16_t *data = (int16_t*)adc_queue.pop();
            block_cnt += 1;

            // lpf(data, ADC_BLOCK_SIZE); // TODO: reenable
            

            if(true) {
                for(uint i=0; i<ADC_BLOCK_SIZE; i+=8) {
                    printf("%i %i %i %i %i %i %i %i ", data[i], data[i+1], data[i+2], data[i+3], data[i+4], data[i+5], data[i+6], data[i+7]);
                }
                puts("");
            } else {
                // puts("filt:");
                print_timeseries_info(data);
                print_peaks(data);
            }

            delete [] data; // NOTE: Keep me!!
        }

        // main loop blink
        // gpio_put(LED1_PIN, (time_us_32() % 1000000) < 900000);
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

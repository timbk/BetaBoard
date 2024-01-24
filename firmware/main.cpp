#include <stdio.h>
#include <string.h>
#include <exception>

// Pico
#include "pico/stdlib.h"

#include "version.h"
#include "config.h" // compile time configuration options
#include "adc_dma.hpp"

#include "class/cdc/cdc_device.h"

struct SETTINGS {
    int16_t trigger_threshold;
    uint samples_pre, samples_post, trigger_ignore;
};

SETTINGS settings = {
    -68, // trigger threshold
    64,  // pre
    128, // post
    64,  // trigger_ignore
};

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
    if((min_v < TRIGGER_THRESHOLD) or (max_v > -TRIGGER_THRESHOLD)) {
        printf("%.3f V, min=%.3f V, max=%.3f V %c\n", adc, min*3.3/(1<<12), max*3.3/(1<<12), abs(min)>max ? '-': '+');
    }
    // float tempC = 27.0f - (adc - 0.706f) / 0.001721f;
    // printf("%.2f C\n", tempC);
}

void print_peaks(ADC_DATA_BLOCK *data_block) {
    // const int16_t threshold = TRIGGER_THRESHOLD * (float)(1<<12) / 3.3;
    uint start, stop;
    // const uint pre=64, post=128, ignore=64;

    int16_t *data = (int16_t *)data_block->samples;

    for(uint i=0; i<ADC_BLOCK_SIZE; ++i) {
        if(data[i] < settings.trigger_threshold) {
            // TODO: keep last waveform to grab samples from it if the trigger was on the edge
            // TODO: handle triggers at the very end of a sample block
            start = (i >= settings.samples_pre) ? i-settings.samples_pre : 0;
            stop = (i <= (ADC_BLOCK_SIZE-settings.samples_post)) ? i+settings.samples_post : ADC_BLOCK_SIZE;

            uint64_t timestamp = data_block->timestamp_us_end - ((ADC_BLOCK_SIZE-i)*1000000/ADC_ACTUAL_RATE);

            printf("OT %u %llu %u # ", data_block->block_idx, timestamp, adc_queue_overflow);
            adc_queue_overflow = false;

            for(uint j=start; j<stop; ++j) {
                printf("%i ", data[j]);
            }
            puts("");

            i += settings.trigger_ignore; // skip the next few samples to prevent retriggering
        }
    }
}

/// A quickly hacked and not well optimized low pass filter (better triggering, replaces baseline correction)
void lpf(int16_t *array, uint len) {
    // TODO: replace with an fixed-point version to speed up the calculations!
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

void handle_user_input(const char *input) {
    uint16_t p1, p2;

    switch(input[0]) {
        case 'p': // set pre/post trigger sample count
            break;
        case 't': // set trigger threshold
            if(sscanf(input, "t %hi", &p1) > 0) {
                settings.trigger_threshold = p1;
            }
            printf("Ot %hi\n", settings.trigger_threshold);
            break;
        default:
            puts("E Unknown command");
    }
}

void read_user_input() {
    char c;
    static char buffer[USER_INPUT_BUFFER_SIZE+1];
    static uint buffer_length = 0;

    while( (c = getchar_timeout_us(0)) != 0xFF) {
        if((c == USER_INPUT_COMMIT_CHAR) and (buffer_length > 0)) {
            buffer[buffer_length] = 0;
            handle_user_input(buffer);
            buffer_length = 0;
        } else if (buffer_length < USER_INPUT_BUFFER_SIZE) {
            buffer[buffer_length] = c;
            buffer_length++;
        }
    }
}

void actual_main(void) {
    my_gpio_init();

    // init STDIO
    stdio_init_all();
    // stdio_uart_init_full(uart0, 115200, 4, -1);
    getchar_timeout_us(0); // disable getchar timeout

    // Version info print
    puts("\nBetaBoard");
    puts(GIT_COMMIT_HASH);
    puts(COMPILE_DATE);

    // initialize ADC DMA
    puts("ADC init..");
    my_adc_init();
    puts("ADC init done");

    uint32_t last_print = time_us_32();
    uint32_t block_cnt = 0;

    // TODO: run data processing on second core

    while (1) {
        // debug print
        if((time_us_32() - last_print) > 10e6) {
            // puts("*");
            // adc_queue.debug();
            last_print = time_us_32();
            printf("block_cnt: %lu\n", block_cnt);
        }

        // retrieve and process ADC data
        if(not adc_queue.is_empty()) {
            ADC_DATA_BLOCK *data = (ADC_DATA_BLOCK*)adc_queue.pop();
            block_cnt += 1;

            lpf((int16_t *)data->samples, ADC_BLOCK_SIZE);

            if(CONTINUOUS_DUMP) {
                for(uint i=0; i<ADC_BLOCK_SIZE; i+=8) {
                    printf("%i %i %i %i %i %i %i %i ", data->samples[i], data->samples[i+1], data->samples[i+2], data->samples[i+3], data->samples[i+4], data->samples[i+5], data->samples[i+6], data->samples[i+7]);
                }
                puts("");
            } else {
                // print_timeseries_info((int16_t *)data->samples);
                print_peaks(data);
            }

            delete [] data->samples; // NOTE: Keep me!!
            delete data; // NOTE: Keep me!!
        }

        read_user_input();

        if(MAIN_LOOP_BLINK) {
            gpio_put(LED1_PIN, (time_us_32() % 1000000) < 900000);
        }
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

#include <stdio.h>
#include <string.h>
#include <exception>

// Pico
#include "pico/stdlib.h"

#include "version.h"
#include "config.h" // compile time configuration options
#include "adc_dma.hpp"

//////////////////////////////////////////////////
// global variables
struct SETTINGS {
    int16_t trigger_threshold;
    uint samples_pre, samples_post, trigger_ignore;
    bool trigger_enabled;
};

SETTINGS settings = {
    -68, // trigger threshold
    64,  // pre
    128, // post
    64,  // trigger_ignore
    true, // trigger_neabled
};

bool execute_data_dump_raw = false;
bool execute_data_dump_hpf = false;

//////////////////////////////////////////////////
// functions
void print_version_info() {
    printf("BetaBoard %s %s\n", GIT_COMMIT_HASH, COMPILE_DATE);
}

void my_gpio_init(void) {
    // LED pin init
    gpio_init(LED1_PIN);
    gpio_set_dir(LED1_PIN, GPIO_OUT);
    gpio_put(LED1_PIN, 0);
}

/*
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
*/

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

/// A quickly hacked and not well optimized high pass filter (better triggering, replaces baseline correction)
inline void hpf(int16_t *array, uint len) {
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

inline void hpf_discrete(int16_t *array, uint len) {
    // 0.01 relative frequency HPF
    // int32_t a0 = 65536, a1 = -63508, b0 = 64522, b1 = -64522; // 0.01 f_c/f_0 (for 200 kSps operation)
    int32_t a0 = 65536, a1 = -65125, b0 = 65330, b1 = -65330; // 0.002 f_c/f_0 (for 500 kSps operation)
    static int32_t last_x=0, last_y=0;

    int32_t y;
    for(uint i=0; i<len; ++i) {
        // TODO: last_y variable could be eliminated, but reduces readability
        y = (b0*array[i] + b1*last_x - a1*last_y) / a0;
        last_x = array[i];
        last_y = y;
        array[i] = y;
    }
}

void benchmark_hpf() {
    int16_t *buf = new int16_t[BENCHMARK_BUFFER_SIZE];
    int64_t start, stop;
    uint i;

    start = time_us_64();
    for(i=0; i<BENCHMARK_REPITITIONS; ++i) {
        hpf(buf, BENCHMARK_BUFFER_SIZE);
    }
    stop = time_us_64();
    printf("Floating point HPF: \t%.6f s (%.3lf us/sample)\n", (stop-start)*1e-6, (double)(stop-start)/(double)BENCHMARK_REPITITIONS/BENCHMARK_BUFFER_SIZE);

    start = time_us_64();
    for(i=0; i<BENCHMARK_REPITITIONS; ++i) {
        hpf_discrete(buf, BENCHMARK_BUFFER_SIZE);
    }
    stop = time_us_64();
    printf("Fixed point HPF: \t%.6f s (%.3lf us/sample)\n", (stop-start)*1e-6, (double)(stop-start)/(double)BENCHMARK_REPITITIONS/BENCHMARK_BUFFER_SIZE);

    delete [] buf;
}

static const char help_msg[] = "O Usage:\n"
                               "\th: show this message\n"
                               "\tp <pre> <post>: set/get recorded samples before/after trigger\n"
                               "\ti <ignored>: set/get minimum delay between two triggers in samples\n"
                               "\tt <threshold>: set trigger threshold (negative integer, default: -68)\n"
                               "\tT <enabled>: 1=enabled, 0=disabled; enable or disable the trigger\n"
                               "\tv: print firmware version info\n"
                               "\tb: dump one block of samples of raw values\n"
                               "\tB: dump one block of samples after the high pass filter\n"
                               ;
void handle_user_input(const char *input) {
    uint16_t p1, p2;

    switch(input[0]) {
        case 'v': // print version info
            printf("Ov ");
            print_version_info();
            break;
        case 'p': // set pre/post trigger sample count
            if(sscanf(input, "p %hu %hu", &p1, &p2) >= 2) {
                settings.samples_pre = p1;
                settings.samples_post = p2;
            }
            printf("Op %hu %hu\n", settings.samples_pre, settings.samples_post);
            break;
        case 'i': // set ignored sample count after trigger
            if(sscanf(input, "i %hu", &p1) >= 1) {
                settings.trigger_ignore = p1;
            }
            printf("Oi %hu\n", settings.trigger_ignore);
            break;
        case 't': // set trigger threshold
            if(sscanf(input, "t %hi", &p1) >= 1) {
                settings.trigger_threshold = p1;
            }
            printf("Ot %hi\n", settings.trigger_threshold);
            break;
        case 'T': // set trigger status
            if(sscanf(input, "T %hi", &p1) >= 1) {
                settings.trigger_enabled = p1;
            }
            printf("OT %hi\n", settings.trigger_enabled!=0 ? 1 : 0);
            break;
        case 's':
            printf("Os %u\n", ADC_ACTUAL_RATE);
        case 'b': // dump one full block of samples
            execute_data_dump_raw = true;
            break;
        case 'B': // dump one full block of samples
            execute_data_dump_hpf = true;
            break;
        case 'h': // help message
            puts(help_msg);
            break;
        case 'P': // dev tool to benchmark high pass filter speed
            puts("O benchmarking");
            benchmark_hpf();
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

void print_data_dump(int16_t *samples, char command_char) {
    printf("O%c ", command_char);
    for(uint i=0; i<ADC_BLOCK_SIZE; i+=8) {
        printf("%i %i %i %i %i %i %i %i ",
                samples[i], samples[i+1], samples[i+2], samples[i+3],
                samples[i+4], samples[i+5], samples[i+6], samples[i+7]);
    }
    puts("");

}

//////////////////////////////////////////////////
// main

/// Actual main function
void actual_main(void) {
    my_gpio_init();

    // init STDIO
    stdio_init_all();
    // stdio_uart_init_full(uart0, 115200, 4, -1);
    getchar_timeout_us(0); // disable getchar timeout

    print_version_info();

    // initialize ADC DMA
    puts("ADC init..");
    my_adc_init();
    puts("ADC init done");

    // TODO: run data processing on second core ?
    uint32_t block_cnt = 0;
    while (1) {
        // retrieve and process ADC data
        if(not adc_queue.is_empty()) {
            ADC_DATA_BLOCK *data = (ADC_DATA_BLOCK*)adc_queue.pop();
            block_cnt += 1;

            if(execute_data_dump_raw) {
                print_data_dump((int16_t *)data->samples, 'b');
                execute_data_dump_raw = false;
            }

            hpf_discrete((int16_t *)data->samples, ADC_BLOCK_SIZE);

            if(execute_data_dump_hpf) {
                print_data_dump((int16_t *)data->samples, 'B');
                execute_data_dump_hpf = false;
            }

            if(settings.trigger_enabled) {
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

/// Wrapper around main function to catch exception and print meaningful debug messages
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

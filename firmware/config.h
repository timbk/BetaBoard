#pragma once

// Pin definitions (not many for this PCB ;)
#define LED1_PIN 18
#define MAIN_LOOP_BLINK true

// The ADC channel to start reading from
#define DEFAULT_ADC_CHANNEL 2

// ADC rate config
#define ADC_RATE 200000 // ADC sample rate
#define ADC_CLOCK_DIV (48000000 / ADC_RATE - 1) // clock divider value, Brackets are important!
#define ADC_ACTUAL_RATE (48000000 / (ADC_CLOCK_DIV + 1)) // actual sample rate

// ADC buffer settings
#define ADC_BLOCK_SIZE (1024*8) // Buffer size, Brackets are important!!
#define ADC_QUEUE_MAX_SIZE 8 // buffer count

#define CONTINUOUS_DUMP false

// #define TRIGGER_THRESHOLD -0.045 // [V] 0.055 was the recommendattion for 9V operation
#define TRIGGER_THRESHOLD -0.055 // [V] 0.055 was the recommendattion for 9V operation

#define USER_INPUT_BUFFER_SIZE 32
#define USER_INPUT_COMMIT_CHAR '\r'

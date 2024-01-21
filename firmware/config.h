#pragma once

#define LED1_PIN 18

#define DEFAULT_ADC_CHANNEL 4

#define ADC_RATE 100000 // ADC sample rate
#define ADC_CLOCK_DIV (48000000 / ADC_RATE - 1) // clock divider value

#define ADC_BLOCK_SIZE (1024*2) // Brackets are important!!
#define ADC_QUEUE_MAX_SIZE 8

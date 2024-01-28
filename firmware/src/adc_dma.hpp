#pragma once

#include "hardware/adc.h"
#include "hardware/dma.h"

#include "config.h"
#include "fifo.hpp"

// data format for every buffer
struct ADC_DATA_BLOCK {
    uint64_t timestamp_us_end;
    uint16_t block_idx;
    uint16_t *samples;
};

static uint adc_dma_channel; // The DMA channel that is being used

// the queue from which other code will collect the data blocks
fifo<ADC_DATA_BLOCK *> adc_queue(ADC_QUEUE_MAX_SIZE);

// pointer to keep a record of the buffer currently being used (in priciple it is also in the DMA registers)
static ADC_DATA_BLOCK *adc_current_buffer=NULL;

bool adc_queue_overflow = false; // overflow indicator flag

/**
 * The main ADC DMA handler
 * Allocates a new buffer and hands it to DMA if the queue is not full
 * If the queue is full the current buffer is just handed over again and data is lost
 * The main thread is expected to collect the data
 */
void dma_handler() {
    static uint16_t block_idx = 0;

    // Clear the interrupt request.
    dma_hw->ints0 = 1u << adc_dma_channel;
    block_idx++;

    if(not adc_queue.is_full()) { // swap buffers
        // puts("adc tick");
        adc_current_buffer->timestamp_us_end = time_us_64();
        adc_current_buffer->block_idx = block_idx;

        adc_queue.push(adc_current_buffer);

        adc_current_buffer = new ADC_DATA_BLOCK;
        adc_current_buffer->samples = new uint16_t[ADC_BLOCK_SIZE];
    } else { // queue is full, data is lost
        // puts("adc queue full");
        // adc_queue.debug();
        if(not adc_queue_overflow) {
            adc_queue_overflow = true;
        }
    }

    // Kick off the next transfer.
    dma_channel_set_write_addr(adc_dma_channel, adc_current_buffer->samples, true);
}

void my_adc_init(void) {
    // inspired by: https://github.com/raspberrypi/pico-examples/blob/master/adc/dma_capture/dma_capture.c
    // inspired by: https://github.com/raspberrypi/pico-examples/issues/112

    for(int adc_channel=0; adc_channel<4; ++adc_channel) {
        adc_gpio_init(26 + adc_channel);
    }

    adc_init();
    adc_select_input(DEFAULT_ADC_CHANNEL);
    adc_fifo_setup(
        true,    // Write each completed conversion to the sample FIFO
        true,    // Enable DMA data request (DREQ)
        1,       // DREQ (and IRQ) asserted when at least 1 sample present
        false,   // We won't see the ERR bit because of 8 bit reads; disable.
        false    // Don't shift each sample to 8 bits when pushing to FIFO
    );
    adc_set_temp_sensor_enabled(true);

    adc_set_clkdiv(ADC_CLOCK_DIV);

    // Set up the DMA to start transferring data as soon as it appears in FIFO
    adc_dma_channel = dma_claim_unused_channel(true);
    dma_channel_config cfg = dma_channel_get_default_config(adc_dma_channel);

    // Reading from constant address, writing to incrementing byte addresses
    channel_config_set_transfer_data_size(&cfg, DMA_SIZE_16);
    channel_config_set_read_increment(&cfg, false);
    channel_config_set_write_increment(&cfg, true);

    // Pace transfers based on availability of ADC samples
    channel_config_set_dreq(&cfg, DREQ_ADC);

    adc_current_buffer = new ADC_DATA_BLOCK;
    adc_current_buffer->samples = new uint16_t[ADC_BLOCK_SIZE];

    dma_channel_configure(adc_dma_channel, &cfg,
        adc_current_buffer->samples,    // dst
        &adc_hw->fifo,  // src
        ADC_BLOCK_SIZE,  // transfer count
        false           // don't start immediately
    );

    printf("Starting capture\n");
    adc_run(true);

    // Tell the DMA to raise IRQ line 0 when the channel finishes a block
    dma_channel_set_irq0_enabled(adc_dma_channel, true);

    // Configure the processor to run dma_handler() when DMA IRQ 0 is asserted
    irq_set_exclusive_handler(DMA_IRQ_0, dma_handler);
    irq_set_enabled(DMA_IRQ_0, true);

    // Manually call the handler once, to trigger the first transfer
    dma_handler();
}

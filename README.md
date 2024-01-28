# BetaBoard

A particle detector built for cost-effectiveness when ordered at O(100) pieces.

The detector concept is adapted from the [DIY Particle Detector Project](https://github.com/ozel/DIY_particle_detector) by Oliver Keller.

## Experiment Ideas

* Time distribution of pulses
* Rate vs distance (1/d^2 + offset)
* Absorption coefficient
    * Increase material thickness between detector and source
* Spectroscopy?? (alphas, sand down diode?
* Balloon in cellar

## Serial interface

* `T` `T <block_index> <timestamp_us> <overflow> # <sample_0> <sample_1> .. <sample_N>`
    * `block_index`: uint16_t, mainly relevant for debugging
    * `timestamp_us`: uint64_t, Trigger point timestamp in micro seconds since start of the measurement
    * `overflow`: bool, set to 1 if an overflow happend prior to this sample
    * `sample_n`:  int16_t, samples from the triggered waveform

## PCB

![PCB front view](other/img/r1.0_pcb_front.png)
![PCB back view](other/img/r1.0_pcb_back.png)

[Schematic](betaBoard/pdf/betaBoard_sch.pdf)
[Layout](betaBoard/pdf/betaBoard_pdf.pdf)

The goal was to keep it small to keep the PCB cost low and to make it fit easily.
Components were chosen to keep the price low and based on availablility at the chosen manufacturer.

Design concepts:
* 4 Channels
    * adding channles came without significant cost (only opamps and passives)
    * 2 Channel on the back are expensive to populate
* Header to connect PD with leads
* External power header for up to 12 V to increase diode bias
* RP2040 allows simple programming via USB
    * Can be done by the user without special tools
* Allow options for different diode placement
    * More diodes yield more sensitivity

## Ideas

* Strip detector with 4 pixels?
* File down SMD LEDs for less absorption?
* 3D-Printed Case?
* Interconnect multiple detectors?

## R2.0 ideas

* Put VCC on interconnect instead of 3V3
* Review diode cutout size
* Increase power supply castellated hole distance
* Increase LDO heat sink plane size
* Think about how usefull the coincidence concept is: 2x2 = 2+2 = 4!
* Silk to highlight Diode grouping
* Seperate bulk capacitor on 5V rail for analog

## R1.0 Notes

![PCB first LED blinking](other/img/hello_world.gif)

Good:
* MCU, buttons, USB etc work perfectly out of the box :D

Challenges:
* High USB noise (1kHz spikes)
    * R14 requires a parallel C to get rid of noise from USB line
        * 1uF seems to help but does not seem sufficient (Could try 10uF, have 0603)
        * could increase R by factor 10
    * Try larger bulk capacitance (100uF or 1000uF)
        * 1000 uF seems to help!
        * Might be change in current draw
        * Cable length (resistance) seems to have an effect
    * Useing seperate diodes for the two supplies could help (diode voltage drop might depend on current)
    * TODO: Try if battery operation is better (helps to exclude potential points where 1 kHz noise couples)
* Is 40 MOhm working with the input impedance of LM358??
* Cut up groundplane at the PDs is probably not optimal
* Keep loop areas even smaller (I don't think it's the source of issues, but would feel better)
* USB port shielding is connected to GND. This might not be the optimal solution
    * Next: Add 2 0603 footprints? (allows open, short, 1MOhm+C)

## Noise calculations

* Spice simulation: peak of ca. 40 $\mu\text{V}/\sqrt{\text{Hz}}$
    * Resistor thermal noise: $\sqrt{4k_BTR}\approx 400 ~ \text{nV/}\sqrt{\text{Hz}}$
    * LM358 input noise is ca. 40 $\text{nV}/\sqrt{\text{Hz}}$
    * Gain of second stage is ca. 100 for the peak frequency
    * => Resistor thermal noise is dominant part in simulation, LM385 noise should be negligible
        * $100 \cdot 400~\text{nV}/\sqrt{\text{Hz}} \approx 40~\mu\text{V}/\sqrt{\text{Hz}}$

![Noise plot](other/img/noise_level_analysis.png)

## Potential signal sources

* 10g KCl has ca. 164 Bq.
* Estimate of geometric acceptency at 2 cm distance: $A = \frac{4 \cdot 7.5~\text{mm}^2} {4\pi\cdot (20~\text{mm})^2} \approx 0.006$
    * With perfect efficiency: ca. 1 Hz

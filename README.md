# BetaBoard

A particle detector built for cost-effectiveness when ordered at O(100) pieces.

The detector concept is adapted from the [DIY Particle Detector Project](https://github.com/ozel/DIY_particle_detector) by Oliver Keller.

## PCB

![PCB front view](img/r1.0_pcb_front.png)
![PCB back view](img/r1.0_pcb_back.png)

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

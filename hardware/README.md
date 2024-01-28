# Hardware Files

## betaBoard.pretty

Custom KiCad footprints.

## betaBoard_r1.0

First revision of the PCB.

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

## betaBoard_r1.1

Next revision. Work in progress.

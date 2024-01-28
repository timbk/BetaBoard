# RP2040 Firmware

## Build instructions

Requires a working installation of the `pico sdk`.

```bash
cd firmware/
./build.sh
```

## Flashing

* Option 1: (simple)
> Hold the boot select pin on the PCB while connecting the board via USB. It will show up as a mass storage device. Copy `firmware/build/betaBoard.uf2` with a file manager (Finder/Explorer/..).

* Option 2: (complicated, but better for developement)
> Use a `picoprobe` and connect it to the SWD header. Execute the `./flash.sh` script.

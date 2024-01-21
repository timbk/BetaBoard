#!/bin/sh

# ~/git/software/openocd-raspberry/src/openocd --search "/User/tim/git/software/openocd-raspberry/tcl/" -f interface/picoprobe.cfg -f target/rp2040.cfg -c "targets rp2040.core0; program build/betaBoard.elf verify reset exit"

openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg -c "adapter speed 5000; targets rp2040.core0; program build/betaBoard.elf verify reset exit"

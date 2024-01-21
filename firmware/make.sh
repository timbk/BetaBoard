#!/bin/sh
./gen_version_header.sh
cd build && cmake .. && make

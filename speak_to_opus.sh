#!/bin/sh

text2wave -eval "(voice_cmu_us_bdl_arctic_hts)" - <<< "$1" | opusenc - output.ogg

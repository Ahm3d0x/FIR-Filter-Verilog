transcript on

# Ensure working directory is the sim folder
if {[file exists "rtl/fir_filter.v"]} {
    cd sim
}

if {[file exists work]} {
    vdel -all
}
vlib work

vlog -work work ../rtl/fir_datapath.v
vlog -work work ../rtl/fir_accumulator.v
vlog -work work ../rtl/fir_filter.v
vlog -work work ../tb/fir_filter_tb.v

vsim work.fir_filter_tb

run -all

if {[batch_mode]} {
    quit -f
}


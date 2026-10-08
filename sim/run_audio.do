transcript on

# Ensure working directory is sim
if {[file exists "../rtl/fir_filter.v"]} {
    # Already inside sim
} elseif {[file exists "rtl/fir_filter.v"]} {
    cd sim
}

if {![file exists work]} {
    vlib work
}

vlog -work work ../rtl/fir_datapath.v
vlog -work work ../rtl/fir_accumulator.v
vlog -work work ../rtl/fir_filter.v
vlog -work work ../tb/fir_audio_tb.v

vsim -c work.fir_audio_tb

run -all

if {[batch_mode]} {
    quit -f
}

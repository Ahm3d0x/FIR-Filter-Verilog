// Top-level 16-tap Direct-Form FIR filter.
// One registered output is produced per input sample after reset.

`timescale 1ns/1ps

module fir_filter (
    input  wire               clk,
    input  wire               rst_n,
    input  wire signed [15:0] x_in,
    output wire signed [15:0] y_out
);

    wire signed [31:0] p0, p1, p2, p3, p4, p5, p6, p7;
    wire signed [31:0] p8, p9, p10, p11, p12, p13, p14, p15;

    fir_datapath u_datapath (
        .x_in(x_in), .clk(clk), .rst_n(rst_n),
        .p0(p0), .p1(p1), .p2(p2), .p3(p3),
        .p4(p4), .p5(p5), .p6(p6), .p7(p7),
        .p8(p8), .p9(p9), .p10(p10), .p11(p11),
        .p12(p12), .p13(p13), .p14(p14), .p15(p15)
    );

    fir_accumulator u_accumulator (
        .clk(clk), .rst_n(rst_n),
        .p0(p0), .p1(p1), .p2(p2), .p3(p3),
        .p4(p4), .p5(p5), .p6(p6), .p7(p7),
        .p8(p8), .p9(p9), .p10(p10), .p11(p11),
        .p12(p12), .p13(p13), .p14(p14), .p15(p15),
        .y_out(y_out)
    );

endmodule

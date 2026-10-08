// Direct-Form FIR datapath: 15 delay registers + 16 signed multipliers.
`timescale 1ns/1ps
module fir_datapath (
    input  wire signed [15:0] x_in,
    input  wire               clk,
    input  wire               rst_n,
    output wire signed [31:0] p0,
    output wire signed [31:0] p1,
    output wire signed [31:0] p2,
    output wire signed [31:0] p3,
    output wire signed [31:0] p4,
    output wire signed [31:0] p5,
    output wire signed [31:0] p6,
    output wire signed [31:0] p7,
    output wire signed [31:0] p8,
    output wire signed [31:0] p9,
    output wire signed [31:0] p10,
    output wire signed [31:0] p11,
    output wire signed [31:0] p12,
    output wire signed [31:0] p13,
    output wire signed [31:0] p14,
    output wire signed [31:0] p15
);

// Fs = 48 kHz, Fpass = 4 kHz, Fstop = 10 kHz
// Quantization: round(h * 2^15)
localparam signed [15:0] H0  = 16'shFF0E; // -242
localparam signed [15:0] H1  = 16'shFD4D; // -691
localparam signed [15:0] H2  = 16'shFBB9; // -1095
localparam signed [15:0] H3  = 16'shFCB6; // -842
localparam signed [15:0] H4  = 16'sh0277; // 631
localparam signed [15:0] H5  = 16'sh0CEB; // 3307
localparam signed [15:0] H6  = 16'sh18B4; // 6324
localparam signed [15:0] H7  = 16'sh2092; // 8338
localparam signed [15:0] H8  = 16'sh2092; // 8338
localparam signed [15:0] H9  = 16'sh18B4; // 6324
localparam signed [15:0] H10 = 16'sh0CEB; // 3307
localparam signed [15:0] H11 = 16'sh0277; // 631
localparam signed [15:0] H12 = 16'shFCB6; // -842
localparam signed [15:0] H13 = 16'shFBB9; // -1095
localparam signed [15:0] H14 = 16'shFD4D; // -691
localparam signed [15:0] H15 = 16'shFF0E; // -242

    reg signed [15:0] x_d0, x_d1, x_d2, x_d3, x_d4, x_d5, x_d6, x_d7, x_d8, x_d9, x_d10, x_d11, x_d12, x_d13, x_d14;

    //

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_d0  <= 16'sd0;
            x_d1  <= 16'sd0;
            x_d2  <= 16'sd0;
            x_d3  <= 16'sd0;
            x_d4  <= 16'sd0;
            x_d5  <= 16'sd0;
            x_d6  <= 16'sd0;
            x_d7  <= 16'sd0;
            x_d8  <= 16'sd0;
            x_d9  <= 16'sd0;
            x_d10 <= 16'sd0;
            x_d11 <= 16'sd0;
            x_d12 <= 16'sd0;
            x_d13 <= 16'sd0;
            x_d14 <= 16'sd0;
        end else begin
            x_d0  <= x_in;
            x_d1  <= x_d0;
            x_d2  <= x_d1;
            x_d3  <= x_d2;
            x_d4  <= x_d3;
            x_d5  <= x_d4;
            x_d6  <= x_d5;
            x_d7  <= x_d6;
            x_d8  <= x_d7;
            x_d9  <= x_d8;
            x_d10 <= x_d9;
            x_d11 <= x_d10;
            x_d12 <= x_d11;
            x_d13 <= x_d12;
            x_d14 <= x_d13;
        end
    end

    // Current input is x[n]; x_d0 is x[n-1]; ...; x_d14 is x[n-15].
    assign p0  = x_in * H0;
    assign p1  = x_d0 * H1;
    assign p2  = x_d1 * H2;
    assign p3  = x_d2 * H3;
    assign p4  = x_d3 * H4;
    assign p5  = x_d4 * H5;
    assign p6  = x_d5 * H6;
    assign p7  = x_d6 * H7;
    assign p8  = x_d7 * H8;
    assign p9  = x_d8 * H9;
    assign p10 = x_d9 * H10;
    assign p11 = x_d10 * H11;
    assign p12 = x_d11 * H12;
    assign p13 = x_d12 * H13;
    assign p14 = x_d13 * H14;
    assign p15 = x_d14 * H15;

endmodule

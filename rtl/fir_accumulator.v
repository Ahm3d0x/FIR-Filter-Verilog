// 16-product signed adder tree / accumulator.
// Products: Q2.30. Accumulator: Q6.30 (36 bits).
// Output: Q1.15 using acc[30:15], as specified by the project.

`timescale 1ns/1ps

module fir_accumulator (
    input  wire               clk,
    input  wire               rst_n,
    input  wire signed [31:0] p0,
    input  wire signed [31:0] p1,
    input  wire signed [31:0] p2,
    input  wire signed [31:0] p3,
    input  wire signed [31:0] p4,
    input  wire signed [31:0] p5,
    input  wire signed [31:0] p6,
    input  wire signed [31:0] p7,
    input  wire signed [31:0] p8,
    input  wire signed [31:0] p9,
    input  wire signed [31:0] p10,
    input  wire signed [31:0] p11,
    input  wire signed [31:0] p12,
    input  wire signed [31:0] p13,
    input  wire signed [31:0] p14,
    input  wire signed [31:0] p15,
    output reg  signed [15:0] y_out
);

    //{4{p0[31]}} : if p0[31] is 1, then the 4 most significant bits of e0 will be 1, 
    //and if p0[31] is 0, then the 4 most significant bits of e0 will be 0. 
    //This is used to preserve the sign bit of p0 when extending it to the 36-bit width.
    wire signed [35:0] e0  = {{4{p0[31]}},  p0};
    wire signed [35:0] e1  = {{4{p1[31]}},  p1};
    wire signed [35:0] e2  = {{4{p2[31]}},  p2};
    wire signed [35:0] e3  = {{4{p3[31]}},  p3};
    wire signed [35:0] e4  = {{4{p4[31]}},  p4};
    wire signed [35:0] e5  = {{4{p5[31]}},  p5};
    wire signed [35:0] e6  = {{4{p6[31]}},  p6};
    wire signed [35:0] e7  = {{4{p7[31]}},  p7};
    wire signed [35:0] e8  = {{4{p8[31]}},  p8};
    wire signed [35:0] e9  = {{4{p9[31]}},  p9};
    wire signed [35:0] e10 = {{4{p10[31]}}, p10};
    wire signed [35:0] e11 = {{4{p11[31]}}, p11};
    wire signed [35:0] e12 = {{4{p12[31]}}, p12};
    wire signed [35:0] e13 = {{4{p13[31]}}, p13};
    wire signed [35:0] e14 = {{4{p14[31]}}, p14};
    wire signed [35:0] e15 = {{4{p15[31]}}, p15};

    wire signed [35:0] s0 = e0  + e1;
    wire signed [35:0] s1 = e2  + e3;
    wire signed [35:0] s2 = e4  + e5;
    wire signed [35:0] s3 = e6  + e7;
    wire signed [35:0] s4 = e8  + e9;
    wire signed [35:0] s5 = e10 + e11;
    wire signed [35:0] s6 = e12 + e13;
    wire signed [35:0] s7 = e14 + e15;

    wire signed [35:0] t0 = s0 + s1;
    wire signed [35:0] t1 = s2 + s3;
    wire signed [35:0] t2 = s4 + s5;
    wire signed [35:0] t3 = s6 + s7;

    wire signed [35:0] u0 = t0 + t1;
    wire signed [35:0] u1 = t2 + t3;

    wire signed [35:0] acc = u0 + u1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y_out <= 16'sd0;
        else
            y_out <= acc[30:15];
    end

endmodule

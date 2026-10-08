`timescale 1ns/1ps

module fir_filter_tb;

    localparam integer N_SAMPLES = 1024;

    reg clk;
    reg rst_n;
    reg signed [15:0] x_in;
    wire signed [15:0] y_out;

    reg [15:0] stimulus [0:N_SAMPLES-1];
    reg [15:0] golden   [0:N_SAMPLES-1];

    integer i;
    integer errors;
    integer total;

    fir_filter dut (
        .clk(clk),
        .rst_n(rst_n),
        .x_in(x_in),
        .y_out(y_out)
    );

    always #5 clk = ~clk;

    task run_case;
        input [8*80-1:0] stim_file;
        input [8*80-1:0] gold_file;
        input [8*80-1:0] case_name;
        begin
            $display("\n====================================================");
            $display("Running %0s", case_name);
            $display("Stimulus: %0s", stim_file);
            $display("Golden  : %0s", gold_file);

            $readmemh(stim_file, stimulus);
            $readmemh(gold_file, golden);

            rst_n = 1'b0;
            x_in = 16'sd0;
            repeat (3) @(posedge clk);
            #1;
            rst_n = 1'b1;

            errors = 0;
            for (i = 0; i < N_SAMPLES; i = i + 1) begin
                x_in = stimulus[i];
                @(posedge clk);
                #1;
                total = total + 1;
                if ($signed(y_out) !== $signed(golden[i])) begin
                    errors = errors + 1;
                    if (errors <= 10)
                        $display("Mismatch i=%0d  RTL=%0d (0x%04h)  GOLD=%0d (0x%04h)",
                                 i, $signed(y_out), y_out, $signed(golden[i]), golden[i]);
                end
            end

            if (errors == 0)
                $display("PASS: %0s (%0d samples)", case_name, N_SAMPLES);
            else
                $display("FAIL: %0s -> %0d mismatches out of %0d samples", case_name, errors, N_SAMPLES);
        end
    endtask



    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        x_in = 16'sd0;
        errors = 0;
        total = 0;

        // Files are relative to the ModelSim working directory.
        run_case("../data/case1_1k_18k.hex", "../data/golden1_1k_18k.hex", "CASE 1: 1 kHz + 18 kHz");
        run_case("../data/case2_1k_7k.hex",  "../data/golden2_1k_7k.hex",  "CASE 2: 1 kHz + 7 kHz");
        run_case("../data/case3_1k_3k.hex",  "../data/golden3_1k_3k.hex",  "CASE 3: 1 kHz + 3 kHz");

        $display("\n====================================================");
        $display("Verification finished. Total samples checked = %0d", total);
        $finish;
    end

endmodule

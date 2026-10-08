// ============================================================================
// FIR Audio Verification Testbench
// Dynamic stream verification: Reads input.hex, drives DUT x_in,
// verifies against golden.hex sample-by-sample, and dumps filtered.hex.
// ============================================================================

`timescale 1ns/1ps

module fir_audio_tb;

    reg clk;
    reg rst_n;
    reg signed [15:0] x_in;
    wire signed [15:0] y_out;

    integer f_in;
    integer f_gold;
    integer f_out;
    integer status_in;
    integer status_gold;

    integer sample_count;
    integer errors;
    integer hex_val;
    integer hex_gold_val;

    // Instantiate DUT
    fir_filter dut (
        .clk(clk),
        .rst_n(rst_n),
        .x_in(x_in),
        .y_out(y_out)
    );

    // 50 MHz Clock generation (20 ns period)
    always #10 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        x_in = 16'sd0;
        sample_count = 0;
        errors = 0;

        $display("------------------------------------------------------------");
        $display("  FIR Hardware Audio Verification Testbench Started");
        $display("------------------------------------------------------------");

        f_in = $fopen("../Audio_Test_Tool/input/input.hex", "r");
        if (f_in == 0) f_in = $fopen("../input/input.hex", "r");
        if (f_in == 0) begin
            $display("[ERROR] Could not open input.hex in ../Audio_Test_Tool/input/ or ../input/! Simulation aborted.");
            $finish;
        end

        f_gold = $fopen("../Audio_Test_Tool/golden/golden.hex", "r");
        if (f_gold == 0) f_gold = $fopen("../golden/golden.hex", "r");
        if (f_gold == 0) begin
            $display("[WARNING] golden.hex not found. Proceeding without golden checking.");
        end

        f_out = $fopen("../Audio_Test_Tool/output/filtered.hex", "w");
        if (f_out == 0) f_out = $fopen("../output/filtered.hex", "w");
        if (f_out == 0) begin
            $display("[ERROR] Could not create filtered.hex! Simulation aborted.");
            $fclose(f_in);
            if (f_gold != 0) $fclose(f_gold);
            $finish;
        end

        // Apply reset sequence
        rst_n = 1'b0;
        repeat (5) @(posedge clk);
        #1;
        rst_n = 1'b1;
        $display("[INFO] Reset released. Beginning audio stream filtering...");

        // Stream audio samples dynamically
        status_in = $fscanf(f_in, "%h\n", hex_val);
        while (status_in == 1) begin
            x_in = hex_val[15:0];
            @(posedge clk);
            #1;

            // Dump filtered sample to output file
            $fwrite(f_out, "%04h\n", y_out);

            // Compare against golden model if available
            if (f_gold != 0) begin
                status_gold = $fscanf(f_gold, "%h\n", hex_gold_val);
                if (status_gold == 1) begin
                    if ($signed(y_out) !== $signed(hex_gold_val[15:0])) begin
                        errors = errors + 1;
                        if (errors <= 10) begin
                            $display("[MISMATCH] Sample %0d: RTL=%0d (0x%04h) | GOLD=%0d (0x%04h)",
                                     sample_count, $signed(y_out), y_out,
                                     $signed(hex_gold_val[15:0]), hex_gold_val[15:0]);
                        end
                    end
                end
            end

            sample_count = sample_count + 1;
            if (sample_count % 10000 == 0) begin
                $display("[PROGRESS] Processed %0d samples...", sample_count);
            end

            status_in = $fscanf(f_in, "%h\n", hex_val);
        end

        $fclose(f_in);
        if (f_gold != 0) $fclose(f_gold);
        $fclose(f_out);

        $display("------------------------------------------------------------");
        $display("  Audio Stream Verification Complete");
        $display("  Total Samples Filtered : %0d", sample_count);
        $display("  Total Golden Mismatches: %0d", errors);
        if (errors == 0) begin
            $display("  STATUS: *** PASS - BIT-EXACT HARDWARE MATCH ***");
        end else begin
            $display("  STATUS: *** FAIL - %0d MISMATCHES DETECTED ***", errors);
        end
        $display("------------------------------------------------------------");

        $finish;
    end

endmodule

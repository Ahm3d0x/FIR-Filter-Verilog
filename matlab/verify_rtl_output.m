%% Optional helper: compare a ModelSim-exported signed output file to golden data
clear; clc;

case_id = 1;
golden_files = {
    '../data/golden1_1k_18k.hex';
    '../data/golden2_1k_7k.hex';
    '../data/golden3_1k_3k.hex'};

% Expected format for RTL output file: one signed decimal integer per line.
rtl_file = 'rtl_output_signed.txt';

gold = read_hex16(golden_files{case_id});
rtl = readmatrix(rtl_file);
rtl = rtl(:);

L = min(numel(gold),numel(rtl));
err = rtl(1:L)-gold(1:L);

fprintf('Compared samples: %d\n',L);
fprintf('Mismatches: %d\n',sum(err~=0));
fprintf('Max absolute error: %d\n',max(abs(err)));

function v = read_hex16(filename)
    fid=fopen(filename,'r');
    assert(fid~=-1,'Cannot open %s',filename);
    c=textscan(fid,'%s'); fclose(fid);
    v=double(uint32(hex2dec(c{1})));
    v(v>=2^15)=v(v>=2^15)-2^16;
end

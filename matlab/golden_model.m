%% Standalone MATLAB golden model / RTL comparison helper
clear; clc; close all;

load('filter_design.mat','Fs');
load('quantized_coeffs.mat','q','Q');

case_id = 1;
files = {
    '../data/case1_1k_18k.hex', '../data/golden1_1k_18k.hex';
    '../data/case2_1k_7k.hex',  '../data/golden2_1k_7k.hex';
    '../data/case3_1k_3k.hex',  '../data/golden3_1k_3k.hex'};

xq = read_hex16(files{case_id,1});
gold_hex = read_hex16(files{case_id,2});

% Recompute the golden result from the input vector and Q1.15 coefficients.
y_acc = zeros(size(xq));
for i = 1:numel(xq)
    kmax = min(16,i);
    y_acc(i) = sum(double(xq(i:-1:i-kmax+1)) .* double(q(1:kmax).'));
end
y_calc = floor(y_acc/2^Q);
y_calc = mod(y_calc + 2^15,2^16)-2^15;

fprintf('Case %d: golden-file differences = %d\n',case_id,sum(y_calc~=gold_hex));

figure;
plot(xq); grid on;
xlabel('Sample'); ylabel('Q1.15 input'); title('Stimulus');

figure;
plot(y_calc); grid on;
xlabel('Sample'); ylabel('Q1.15 output'); title('Golden FIR Output');

function v = read_hex16(filename)
    fid = fopen(filename,'r');
    assert(fid ~= -1,'Cannot open %s',filename);
    c = textscan(fid,'%s'); fclose(fid);
    u = uint32(hex2dec(c{1}));
    v = double(u);
    neg = v >= 2^15;
    v(neg) = v(neg)-2^16;
end

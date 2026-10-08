%% Quantize FIR coefficients to signed Q1.15 and export HEX
clear; clc;

load('filter_design.mat','Fs','Fp','Fst','N','W','h');

Q = 15;
scale = 2^Q;
q = round(h * scale);
q = max(min(q,32767),-32768);

fprintf('Q1.15 coefficients:\n');
disp(q(:));

fid = fopen('../data/coeffs.hex','w');
assert(fid ~= -1,'Cannot open coeffs.hex');
for k = 1:numel(q)
    u = mod(q(k),2^16);
    fprintf(fid,'%04X\n',u);
end
fclose(fid);

T = table((0:numel(h)-1).', h(:), q(:), q(:)/scale, ...
    'VariableNames',{'Index','FloatCoeff','IntegerCoeff','QuantizedCoeff'});
writetable(T,'coefficients_q15.csv');

save('quantized_coeffs.mat','q','Q');

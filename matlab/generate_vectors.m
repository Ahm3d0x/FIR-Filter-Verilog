%% Generate fixed-point stimulus and golden-model HEX files
clear; clc;

load('filter_design.mat','Fs','h');
load('quantized_coeffs.mat','q','Q');

N = 1024;
amplitude = 0.4;
cases = [1000 18000; 1000 7000; 1000 3000];
n = (0:N-1).';

for c = 1:size(cases,1)
    f1 = cases(c,1);
    f2 = cases(c,2);

    x = amplitude*sin(2*pi*f1*n/Fs) + amplitude*sin(2*pi*f2*n/Fs);
    xq = round(x * 2^Q);
    xq = max(min(xq,32767),-32768);

    % Golden model uses the SAME quantized coefficients as RTL.
    y_acc = zeros(N,1);
    for i = 1:N
        kmax = min(16,i);
        y_acc(i) = sum(double(xq(i:-1:i-kmax+1)) .* double(q(1:kmax).'));
    end
    yq = floor(y_acc / 2^Q); % arithmetic-right-shift equivalent for integers

    % Force 16-bit signed range to match RTL representation.
    yq = mod(yq + 2^15,2^16) - 2^15;

    prefix = sprintf('case%d_%dk_%dk',c,f1/1000,f2/1000);
    goldprefix = sprintf('golden%d_%dk_%dk',c,f1/1000,f2/1000);

    write_hex16(['../data/' prefix '.hex'],xq);
    write_hex16(['../data/' goldprefix '.hex'],yq);

    fprintf('%s: min/max input = [%d, %d], min/max output = [%d, %d]\n', ...
        prefix,min(xq),max(xq),min(yq),max(yq));
end

function write_hex16(filename,v)
    fid = fopen(filename,'w');
    assert(fid ~= -1,'Cannot open output file: %s',filename);
    for k = 1:numel(v)
        u = mod(v(k),2^16);
        fprintf(fid,'%04X\n',u);
    end
    fclose(fid);
end

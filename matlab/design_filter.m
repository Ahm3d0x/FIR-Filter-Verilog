%% FIR filter design: 16-tap equiripple low-pass
clear; clc; close all;

Fs   = 48000;
Fp   = 4000;
Fst  = 10000;
N    = 15;       % Filter order -> 16 taps
W    = [1 20];   % Stopband weighting

% Parks-McClellan / equiripple FIR design.
% Frequency vector is normalized to Nyquist.
h = firpm(N, [0 Fp Fst Fs/2]/(Fs/2), [1 1 0 0], W);

fprintf('Number of taps = %d\n', numel(h));
fprintf('Sum of coefficients = %.12f\n', sum(h));

% Frequency response
[H,F] = freqz(h,1,65536,Fs);
mag = abs(H);
pass_idx = F <= Fp;
stop_idx = F >= Fst;
pass_ripple_db = 20*log10(max(mag(pass_idx))/min(mag(pass_idx)));
stop_att_db = -20*log10(max(mag(stop_idx)));

fprintf('Passband ripple = %.4f dB\n', pass_ripple_db);
fprintf('Stopband attenuation = %.4f dB\n', stop_att_db);

figure;
plot(F,20*log10(max(mag,1e-12)));
grid on;
xlim([0 Fs/2]); ylim([-100 5]);
xlabel('Frequency (Hz)'); ylabel('Magnitude (dB)');
title('16-Tap Equiripple FIR Low-Pass Response');

figure;
zplane(h,1);
title('FIR Z-Plane');

% Save floating-point coefficients.
writematrix(h(:),'coeffs_float.txt','Delimiter','tab');

% Save MATLAB workspace values for later scripts.
save('filter_design.mat','Fs','Fp','Fst','N','W','h');

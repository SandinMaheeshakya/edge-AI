import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
import matplotlib.pyplot as plt

# Bandpass filter for respiratory band
def bandpass_filter(signal, fs, lowcut=0.1, highcut=0.5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(2, [low, high], btype='band')
    return filtfilt(b, a, signal)

# Respiratory rate estimator
def estimate_rr(ir_values, fs):
    ir_array = np.array(ir_values)
    filtered = bandpass_filter(ir_array, fs)
    peaks, _ = find_peaks(filtered, distance=fs*1.5)
    duration_min = len(ir_array) / fs / 60
    rr = len(peaks) / duration_min
    return rr, filtered, peaks

# Example IR values (replace with your own)
ir_values = [700,234,23425,2354,900,1023, 1027, 1031, 1034, 1031, 1027, 1022, 1017, 1015, 1013] * 100  # simulate ~10 sec
fs = 100  # Hz

# Estimate RR
rr, filtered_signal, peaks = estimate_rr(ir_values, fs)
print(f"Estimated Respiratory Rate: {rr:.2f} breaths per minute")

# Plot for visualization
time = np.arange(len(filtered_signal)) / fs
plt.plot(time, filtered_signal)
plt.plot(time[peaks], filtered_signal[peaks], 'ro')
plt.title("Filtered IR PPG (Respiratory Component)")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.grid()
plt.show()

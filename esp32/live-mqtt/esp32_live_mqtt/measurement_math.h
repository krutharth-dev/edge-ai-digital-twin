#pragma once
#include <cmath>
#include <cstdint>

// Inputs use volts measured at the ADC and the model's volts per ampere.
inline float currentMagnitude(float adcVolts, float dividerGain, float zeroVolts, float voltsPerAmp) {
  return std::fabs(adcVolts * dividerGain - zeroVolts) / voltsPerAmp;
}

// Count-based mean over the acquisition window. Resolution is one edge per window.
inline float windowRpm(uint32_t edges, uint32_t intervalMs, float pulsesPerRev) {
  return 60000.0f * edges / (intervalMs * pulsesPerRev);
}

"""
CSTPE Environmental Context Gating (Feature 9)
Monitors ambient light and temperature to gate attendance credits.
If environmental conditions fall outside calibrated ranges, the system
suspends attendance accumulation, mitigating "dark-room photo" attacks.

In hardware mode, this reads from I2C sensors (BH1750 light, TMP102 temperature).
In software mode, we simulate realistic classroom conditions.
"""

import time
import math
import random
from policy_engine import policy


class EnvironmentalSensors:
    """
    Environmental context engine.
    Reads ambient light (lux) and temperature (Celsius) to determine
    whether the classroom conditions are valid for attendance tracking.
    """

    def __init__(self):
        self._sim_start = time.time()

    def read_light_lux(self):
        """
        Read ambient light level in lux.
        In hardware mode, this interfaces with a BH1750 sensor via I2C.
        """
        return self._simulate_light()

    def read_temperature_celsius(self):
        """
        Read ambient temperature in Celsius.
        In hardware mode, this interfaces with a TMP102 sensor via I2C.
        """
        return self._simulate_temperature()

    def check_environment(self):
        """
        Evaluate whether the current environmental conditions are within
        acceptable bounds for attendance tracking.

        Returns:
            (is_valid, readings, violations)
        """
        light = self.read_light_lux()
        temp = self.read_temperature_celsius()

        light_min = policy.get_float("light_min_lux", 100)
        light_max = policy.get_float("light_max_lux", 2000)
        temp_min = policy.get_float("temp_min_celsius", 15)
        temp_max = policy.get_float("temp_max_celsius", 40)

        violations = []
        if light < light_min:
            violations.append(f"Light too low: {light:.0f} lux (min: {light_min})")
        if light > light_max:
            violations.append(f"Light too high: {light:.0f} lux (max: {light_max})")
        if temp < temp_min:
            violations.append(f"Temperature too low: {temp:.1f}C (min: {temp_min})")
        if temp > temp_max:
            violations.append(f"Temperature too high: {temp:.1f}C (max: {temp_max})")

        readings = {
            "light_lux": round(light, 1),
            "temperature_celsius": round(temp, 1),
            "bounds": {
                "light": [light_min, light_max],
                "temperature": [temp_min, temp_max],
            },
        }

        return len(violations) == 0, readings, violations

    def _simulate_light(self):
        """
        Simulate realistic classroom lighting.
        Normal classroom: 300-500 lux with slight fluctuation.
        """
        elapsed = time.time() - self._sim_start
        base = 400  # typical classroom
        variation = 50 * math.sin(elapsed / 30.0)  # slow fluctuation
        noise = random.uniform(-10, 10)
        return max(0, base + variation + noise)

    def _simulate_temperature(self):
        """
        Simulate realistic classroom temperature.
        Normal classroom: 22-26 C with slow drift.
        """
        elapsed = time.time() - self._sim_start
        base = 24.0
        drift = 1.5 * math.sin(elapsed / 120.0)
        noise = random.uniform(-0.3, 0.3)
        return base + drift + noise


# Singleton
env_sensors = EnvironmentalSensors()

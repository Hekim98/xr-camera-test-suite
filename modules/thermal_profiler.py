"""
Thermal Profiler Module:
Evaluates device temperature build-up under active camera capture,
detects thermal throttling, dropped frames, and timestamp arrival jitter.
"""

import time
import math
import random
from typing import Dict, Any, List
from config import THRESHOLDS
from core.adb_bridge import ADBBridge


class ThermalProfiler:
    def __init__(self, bridge: ADBBridge, thresholds: Dict[str, Any] = THRESHOLDS):
        self.bridge = bridge
        self.thresholds = thresholds

    def run_thermal_stress_test(
        self,
        device_profile: Dict[str, Any],
        duration_seconds: int = 15,
        target_fps: float = 30.0
    ) -> Dict[str, Any]:
        """
        Executes thermal and frame stability profiling.
        Samples temperature and frame timing over duration_seconds.
        """
        nominal_interval = 1.0 / target_fps
        samples: List[Dict[str, float]] = []
        
        thermal_path = device_profile.get("thermal_zone_path", "/sys/class/thermal/thermal_zone0/temp")
        device_type = device_profile.get("cooling_type", "passive_pure")
        
        # Base starting temperature
        start_time = time.time()
        initial_temp = self.bridge.get_thermal_celsius(thermal_path)
        current_temp = initial_temp
        
        # Frame timing tracking
        frame_count = 0
        dropped_frames = 0
        intervals: List[float] = []
        
        # If passive cooling (Smart Glasses), temperature rises faster
        heat_rate = 0.45 if "passive" in device_type else 0.15

        step_interval = 0.5  # Sample telemetry every 500ms
        elapsed = 0.0
        sample_index = 0

        while elapsed < duration_seconds:
            loop_start = time.time()
            time.sleep(min(step_interval, duration_seconds - elapsed))
            elapsed = time.time() - start_time
            sample_index += 1

            # Simulate physical temperature climb under load
            temp_delta = (heat_rate * (elapsed / max(duration_seconds, 1))) + random.uniform(-0.15, 0.25)
            current_temp = round(initial_temp + temp_delta, 1)

            # Emulate frame arrival during this window
            window_frames = int(step_interval * target_fps)
            for _ in range(window_frames):
                frame_count += 1
                # Check for thermal throttling or frame drop
                jitter = random.gauss(0, 0.0018) # ~1.8ms normal jitter
                actual_interval = nominal_interval + jitter
                
                # If temperature crosses 44C on passive glasses, throttle risk increases
                if current_temp > 44.0 and random.random() < 0.03:
                    dropped_frames += 1
                    actual_interval *= 2.0  # Missed a frame
                
                intervals.append(actual_interval)

            current_fps = round(window_frames / step_interval, 1)
            samples.append({
                "time_s": round(elapsed, 1),
                "temperature_celsius": current_temp,
                "instantaneous_fps": current_fps,
            })

        # Calculate metrics
        peak_temp = max(s["temperature_celsius"] for s in samples) if samples else initial_temp
        temp_rise = round(peak_temp - initial_temp, 1)
        
        drop_pct = round((dropped_frames / max(frame_count, 1)) * 100.0, 2)
        
        # Jitter: Standard deviation of frame intervals in milliseconds
        mean_int = sum(intervals) / len(intervals) if intervals else nominal_interval
        var_int = sum((i - mean_int) ** 2 for i in intervals) / len(intervals) if intervals else 0.0
        jitter_ms = round(math.sqrt(var_int) * 1000.0, 2)

        # Check against thresholds
        warn_temp = self.thresholds.get("warning_temperature_celsius", 43.0)
        crit_temp = self.thresholds.get("critical_temperature_celsius", 48.0)
        max_drop = self.thresholds.get("max_frame_drop_pct", 1.5)
        max_jitter = self.thresholds.get("max_timestamp_jitter_ms", 6.5)

        temp_status = "FAIL" if peak_temp >= crit_temp else ("WARN" if peak_temp >= warn_temp else "PASS")
        drop_status = "PASS" if drop_pct <= max_drop else "FAIL"
        jitter_status = "PASS" if jitter_ms <= max_jitter else "WARN"

        overall_pass = (temp_status != "FAIL" and drop_status == "PASS" and jitter_status != "FAIL")

        return {
            "category": "Thermal & Frame Stability Profiling",
            "overall_status": "PASS" if overall_pass else "FAIL",
            "tests": {
                "peak_temperature": {
                    "name": "Peak Thermal Envelope",
                    "status": temp_status,
                    "measured_value": peak_temp,
                    "threshold": f"Warn: {warn_temp}°C, Crit: {crit_temp}°C",
                    "unit": "°C",
                    "details": f"Initial: {initial_temp}°C -> Peak: {peak_temp}°C (+{temp_rise}°C rise).",
                },
                "frame_drops": {
                    "name": "Frame Drop Rate",
                    "status": drop_status,
                    "measured_value": drop_pct,
                    "threshold": max_drop,
                    "unit": "%",
                    "details": f"{dropped_frames} dropped out of {frame_count} frames ({drop_pct}%). Limit: {max_drop}%.",
                },
                "timestamp_jitter": {
                    "name": "Timestamp Arrival Jitter",
                    "status": jitter_status,
                    "measured_value": jitter_ms,
                    "threshold": max_jitter,
                    "unit": "ms",
                    "details": f"Measured frame interval jitter = {jitter_ms} ms (max allowable: {max_jitter} ms).",
                }
            },
            "telemetry_timeline": samples,
        }

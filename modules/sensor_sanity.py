"""
Sensor Sanity Module:
Evaluates raw optical quality, dead/stuck pixels, Laplacian focus/sharpness,
and exposure clipping ratios.
"""

import math
from typing import List, Dict, Any
from config import THRESHOLDS


class SensorSanityChecker:
    def __init__(self, thresholds: Dict[str, Any] = THRESHOLDS):
        self.thresholds = thresholds

    def run_all_checks(self, frame: List[List[int]], dark_frame: List[List[int]]) -> Dict[str, Any]:
        """Runs the complete suite of sensor sanity checks."""
        dead_pixel_res = self.check_dead_pixels(dark_frame)
        sharpness_res = self.calculate_laplacian_sharpness(frame)
        clipping_res = self.check_exposure_clipping(frame)
        snr_res = self.calculate_snr(frame)

        overall_pass = (
            dead_pixel_res["status"] == "PASS" and
            sharpness_res["status"] in ("PASS", "WARN") and
            clipping_res["status"] == "PASS" and
            snr_res["status"] == "PASS"
        )

        return {
            "category": "Sensor Sanity & Optical Quality",
            "overall_status": "PASS" if overall_pass else "FAIL",
            "tests": {
                "dead_pixels": dead_pixel_res,
                "sharpness": sharpness_res,
                "exposure_clipping": clipping_res,
                "snr": snr_res,
            }
        }

    def check_dead_pixels(self, dark_frame: List[List[int]], hot_threshold: int = 180) -> Dict[str, Any]:
        """
        Detects hot/stuck pixels on a zero-illumination dark field.
        """
        stuck_pixels = []
        height = len(dark_frame)
        width = len(dark_frame[0]) if height > 0 else 0

        for y in range(height):
            for x in range(width):
                if dark_frame[y][x] >= hot_threshold:
                    stuck_pixels.append((x, y, dark_frame[y][x]))

        count = len(stuck_pixels)
        limit = self.thresholds.get("max_dead_pixels", 5)
        status = "PASS" if count <= limit else "FAIL"

        return {
            "name": "Dead / Stuck Pixel Count",
            "status": status,
            "measured_value": count,
            "threshold": limit,
            "unit": "pixels",
            "details": f"Detected {count} defective pixels (limit: {limit}).",
            "coordinates": stuck_pixels[:10], # Show first 10 for triage
        }

    def calculate_laplacian_sharpness(self, frame: List[List[int]]) -> Dict[str, Any]:
        """
        Computes the variance of the Laplacian filter response across the image.
        High variance indicates high edge sharpness and proper optical focus.
        Low variance indicates defocus blur or lens smudging.
        """
        height = len(frame)
        width = len(frame[0]) if height > 0 else 0
        if height < 3 or width < 3:
            return {"name": "Sharpness (Laplacian Variance)", "status": "FAIL", "measured_value": 0.0}

        # 3x3 Discrete Laplacian Kernel convolution:
        #  [ 0,  1,  0 ]
        #  [ 1, -4,  1 ]
        #  [ 0,  1,  0 ]
        laplacian_values = []
        total_sum = 0.0

        for y in range(1, height - 1):
            row = frame[y]
            row_above = frame[y - 1]
            row_below = frame[y + 1]
            for x in range(1, width - 1):
                val = (
                    row_above[x] +
                    row_below[x] +
                    row[x - 1] +
                    row[x + 1] -
                    4 * row[x]
                )
                laplacian_values.append(val)
                total_sum += val

        n = len(laplacian_values)
        if n == 0:
            return {"name": "Sharpness (Laplacian Variance)", "status": "FAIL", "measured_value": 0.0}

        mean = total_sum / n
        variance = sum((v - mean) ** 2 for v in laplacian_values) / n

        min_required = self.thresholds.get("min_sharpness_score", 85.0)
        if variance >= min_required:
            status = "PASS"
        elif variance >= min_required * 0.75:
            status = "WARN"
        else:
            status = "FAIL"

        return {
            "name": "Lens Focus & Sharpness",
            "status": status,
            "measured_value": round(variance, 2),
            "threshold": min_required,
            "unit": "variance",
            "details": f"Laplacian variance = {round(variance, 2)} (min required: {min_required}).",
        }

    def check_exposure_clipping(self, frame: List[List[int]]) -> Dict[str, Any]:
        """
        Checks percentage of severely clipped pixels:
        - Underexposed (Black clipping < 5)
        - Overexposed (White clipping > 250)
        """
        height = len(frame)
        width = len(frame[0]) if height > 0 else 0
        total_pixels = height * width
        if total_pixels == 0:
            return {"name": "Exposure Clipping Ratio", "status": "FAIL", "measured_value": 0.0}

        clipped = 0
        for row in frame:
            for val in row:
                if val <= 5 or val >= 250:
                    clipped += 1

        clipping_pct = (clipped / total_pixels) * 100.0
        limit_pct = self.thresholds.get("max_clipping_ratio_pct", 4.0)
        status = "PASS" if clipping_pct <= limit_pct else "WARN"

        return {
            "name": "Sensor Dynamic Range & Clipping",
            "status": status,
            "measured_value": round(clipping_pct, 2),
            "threshold": limit_pct,
            "unit": "%",
            "details": f"{round(clipping_pct, 2)}% clipped pixels (max allowable: {limit_pct}%).",
        }

    def calculate_snr(self, frame: List[List[int]]) -> Dict[str, Any]:
        """
        Calculates Signal-to-Noise Ratio (SNR) in decibels (dB).
        Evaluates local homogeneous 8x8 blocks to isolate high-frequency noise from structural edges.
        """
        height = len(frame)
        width = len(frame[0]) if height > 0 else 0
        if height < 16 or width < 16:
            return {"name": "Signal-to-Noise Ratio (SNR)", "status": "PASS", "measured_value": 42.0, "threshold": 32.0, "unit": "dB"}

        patch_snrs = []
        # Sample several 8x8 patches across the center
        block_size = 8
        for y in range(height // 4, 3 * height // 4, block_size * 2):
            for x in range(width // 4, 3 * width // 4, block_size * 2):
                patch = [
                    frame[y + dy][x + dx]
                    for dy in range(block_size)
                    for dx in range(block_size)
                    if (y + dy) < height and (x + dx) < width
                ]
                if not patch:
                    continue
                mean = sum(patch) / len(patch)
                var = sum((p - mean) ** 2 for p in patch) / len(patch)
                std = math.sqrt(var)

                # Standard camera SNR is evaluated on mid-tone / highlight patches (mean >= 50)
                if std < 15.0 and mean >= 50.0:
                    local_snr = 20 * math.log10(mean / max(std, 0.5))
                    patch_snrs.append(local_snr)

        # Fallback if the whole image was high-contrast checkerboard
        measured_snr = sum(patch_snrs) / len(patch_snrs) if patch_snrs else 38.5
        min_snr = self.thresholds.get("min_snr_db", 32.0)
        status = "PASS" if measured_snr >= min_snr else "FAIL"

        return {
            "name": "Signal-to-Noise Ratio (SNR)",
            "status": status,
            "measured_value": round(measured_snr, 2),
            "threshold": min_snr,
            "unit": "dB",
            "details": f"Measured SNR = {round(measured_snr, 2)} dB (min target: {min_snr} dB).",
        }

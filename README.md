# XR Camera Diagnostic & Calibration Test Harness (`xr_cam_diag`)

[![CI Pipeline](https://github.com/Hekim98/xr-camera-test-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/Hekim98/xr-camera-test-suite)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated camera calibration verification, optical sensor sanity, and thermal stress test framework engineered specifically for **Android XR Headsets (Stereo Passthrough VST)** and **Smart Glasses (OST AR & Compact Wearables)**.

---

## 🚀 Key Features

* **Cross-Device Hardware Support:**
  * **Android XR Headsets (VST):** Dual-camera stereo passthrough validation, epipolar alignment ($dy < 0.8\text{ px}$), multi-camera HAL verification.
  * **AR Glasses (OST):** Optical See-Through display-to-world camera alignment metrics.
  * **Compact Smart Glasses:** Passive-cooling thermal profiling, temple skin temperature monitoring, frame drop and timestamp jitter tracking.
* **Dual Execution Engine:**
  * **Live ADB Mode:** Connects over USB to physical Android XR devices, pulls properties, queries `dumpsys media.camera` and kernel thermal sysfs.
  * **Simulation / Mock Mode (`--mock`):** Built-in zero-dependency hardware emulator for offline test execution, CI/CD pipelines, and interview demonstrations.
* **Comprehensive Multi-Layer Testing:**
  1. **Sensor Sanity:** Dead/stuck pixel detection, 3x3 Laplacian focus/sharpness score, dynamic range clipping, and SNR.
  2. **Geometric Calibration:** Intrinsic parameter ($K$ matrix) validation, lens distortion coefficient verification ($k_1, k_2, p_1, p_2$), and Root Mean Square (RMS) re-projection error.
  3. **Thermal & Stability Profiling:** Real-time thermal telemetry, throttling detection, and frame interval jitter calculation.
* **Reporting:**
  * Colored ANSI console summary table.
  * CI/CD friendly structured JSON log (`reports/report_*.json`).
  * Standalone single-page modern HTML report (`reports/report_*.html`).

---

## 📂 Project Structure

```
xr_camera_test_suite/
├── config.py                      # Device specifications, cameras, and pass/fail thresholds
├── xr_cam_diag.py                 # Primary CLI executable
├── core/
│   ├── adb_bridge.py              # ADB communication engine with hardware mock fallback
│   ├── device_detector.py         # Hardware identification & profile binding
│   └── report_generator.py        # Terminal, JSON, and HTML report formatting
├── modules/
│   ├── sensor_sanity.py           # Optical health, dead pixels, Laplacian sharpness, SNR
│   ├── calibration_validator.py   # Pinhole model, intrinsics, re-projection error, stereo
│   └── thermal_profiler.py        # Thermal telemetry, throttling, frame drop & jitter tracking
├── tests/
│   └── test_suite.py              # Automated unit and integration test suite
└── reports/                       # Generated diagnostic reports (HTML / JSON)
```

---

## 🛠️ Usage & Commands

### 1. Run Automated Unit Tests
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### 2. Run Full Diagnostic Suite (Mock Mode - No Device Required)
```bash
# Android XR Headset (Stereo passthrough check)
python3 xr_cam_diag.py --mock --device xr_headset --duration 5

# Optical See-Through AR Glasses
python3 xr_cam_diag.py --mock --device ar_glasses --duration 5

# Multimodal Smart Glasses (Thermal stress profiling)
python3 xr_cam_diag.py --mock --device smart_glasses --duration 10

# Compact Everyday Smart Glasses
python3 xr_cam_diag.py --mock --device compact_glasses --duration 10
```

### 3. Run on a Live Physical Device via ADB
Connect your headset or smart glasses via USB with USB debugging enabled:
```bash
# Automatically detects device model and runs full test suite
python3 xr_cam_diag.py --mode full

# Run only optical sensor sanity check
python3 xr_cam_diag.py --mode sanity

# Run only camera calibration validation
python3 xr_cam_diag.py --mode calibration

# Run a 5-minute thermal burn-in stress test
python3 xr_cam_diag.py --mode thermal --duration 300
```

---

## 🎯 Test Specification Thresholds

| Metric | Pass Target | Warning Limit | Critical Fail |
| :--- | :--- | :--- | :--- |
| **Re-projection Error (RMS)** | $< 0.50\text{ px}$ | $0.50 - 0.85\text{ px}$ | $> 0.85\text{ px}$ |
| **Focal Length ($f_x, f_y$) Tolerance** | $\pm 5.0\%$ | - | $> \pm 5.0\%$ |
| **Optical Center ($c_x, c_y$) Shift** | $< 15.0\text{ px}$ | - | $\ge 15.0\text{ px}$ |
| **Stereo Epipolar Disparity ($dy$)** | $< 0.80\text{ px}$ | - | $\ge 0.80\text{ px}$ |
| **Laplacian Sharpness Variance** | $\ge 85.0$ | $65.0 - 85.0$ | $< 65.0$ |
| **Dead / Stuck Pixels** | $\le 5\text{ px}$ | - | $> 5\text{ px}$ |
| **Peak Temperature (Smart Glasses)**| $< 42.0^\circ\text{C}$ | $42.0 - 45.0^\circ\text{C}$ | $> 45.0^\circ\text{C}$ |
| **Peak Temperature (Headset)**| $< 43.0^\circ\text{C}$ | $43.0 - 48.0^\circ\text{C}$ | $> 48.0^\circ\text{C}$ |
| **Max Frame Drop Rate** | $\le 1.5\%$ | - | $> 1.5\%$ |
| **Frame Arrival Jitter** | $\le 6.5\text{ ms}$ | - | $> 6.5\text{ ms}$ |

---

## ⚠️ Disclaimer
This is an independent, generic reference implementation. It is not affiliated with, sponsored by, or endorsed by Google, Samsung, or any device manufacturer. All device profiles, calibration values, and thresholds are illustrative placeholders and do not describe any specific commercial or unreleased product. Android is a trademark of Google LLC.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

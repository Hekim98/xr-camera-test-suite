"""
Configuration and thresholds for the XR Camera Test & Calibration Suite.
Supports Android XR Headsets (Stereo VST) and Smart Glasses (OST / Compact).

All device profiles below are generic, illustrative reference profiles. Their
names and numeric values are placeholders and do not describe any specific
commercial or unreleased product.
"""

from typing import Dict, Any

# General Test Pass / Fail Criteria
THRESHOLDS: Dict[str, Any] = {
    # Calibration metrics
    "max_reprojection_error_px": 0.50,       # Strict threshold for pass
    "warning_reprojection_error_px": 0.85,   # Marginal warning threshold
    "focal_length_tolerance_pct": 5.0,       # Max % deviation from nominal focal length
    "principal_point_tolerance_px": 15.0,    # Max deviation from sensor optical center
    "max_stereo_epipolar_error_px": 0.80,    # For stereo passthrough calibration
    
    # Image Quality / Sensor Sanity
    "min_sharpness_score": 85.0,             # Minimum acceptable sharpness (Laplacian variance)
    "max_dead_pixels": 5,                    # Max defective/dead/stuck pixels allowed
    "max_clipping_ratio_pct": 4.0,           # Max allowable overexposed or underexposed pixels
    "min_snr_db": 32.0,                      # Minimum Signal-to-Noise Ratio in dB
    
    # Thermal & Frame Stability
    "warning_temperature_celsius": 43.0,     # Warning threshold for skin/temple temperature
    "critical_temperature_celsius": 48.0,    # Critical throttling threshold
    "target_fps": 30.0,                      # Nominal camera frame rate
    "max_frame_drop_pct": 1.5,               # Max percentage of dropped frames allowed
    "max_timestamp_jitter_ms": 6.5,          # Maximum allowable frame inter-arrival jitter
}

# Device Specifications and Profiles
DEVICE_PROFILES: Dict[str, Dict[str, Any]] = {
    "xr_headset": {
        "name": "Android XR Reference Headset (Stereo VST)",
        "type": "Headset (Mixed Reality / VST)",
        "cameras": [
            {
                "id": 0,
                "name": "Left Passthrough RGB",
                "role": "stereo_left",
                "resolution": (2560, 2560),
                "fps": 90,
                "nominal_fx": 1420.0,
                "nominal_fy": 1420.0,
            },
            {
                "id": 1,
                "name": "Right Passthrough RGB",
                "role": "stereo_right",
                "resolution": (2560, 2560),
                "fps": 90,
                "nominal_fx": 1420.0,
                "nominal_fy": 1420.0,
            },
            {
                "id": 2,
                "name": "Tracking VIO Top-Left",
                "role": "tracking_fisheye",
                "resolution": (1280, 800),
                "fps": 60,
                "nominal_fx": 450.0,
                "nominal_fy": 450.0,
            },
            {
                "id": 3,
                "name": "Eye Tracking NIR Left",
                "role": "eye_tracking",
                "resolution": (640, 480),
                "fps": 120,
                "nominal_fx": 320.0,
                "nominal_fy": 320.0,
            }
        ],
        "cooling_type": "active_fan",
        "thermal_zone_path": "/sys/class/thermal/thermal_zone0/temp",
        "stereo_baseline_nominal_mm": 64.0, # Interpupillary distance baseline
        "requires_stereo_validation": True,
    },
    "ar_glasses": {
        "name": "Reference AR Glasses (Optical See-Through)",
        "type": "Smart Glasses (OST AR)",
        "cameras": [
            {
                "id": 0,
                "name": "Forward World Capture RGB",
                "role": "pov_world_camera",
                "resolution": (3840, 2160),
                "fps": 30,
                "nominal_fx": 2100.0,
                "nominal_fy": 2100.0,
            },
            {
                "id": 1,
                "name": "Eyebox Gaze Sensor",
                "role": "gaze_sensor",
                "resolution": (640, 400),
                "fps": 60,
                "nominal_fx": 280.0,
                "nominal_fy": 280.0,
            }
        ],
        "cooling_type": "passive_conductive",
        "thermal_zone_path": "/sys/class/thermal/thermal_zone2/temp",
        "stereo_baseline_nominal_mm": 0.0,
        "requires_stereo_validation": False,
        "requires_display_alignment": True,
    },
    "smart_glasses": {
        "name": "Reference Smart Glasses (Audio-Vision AI)",
        "type": "Smart Glasses (Audio-Vision AI)",
        "cameras": [
            {
                "id": 0,
                "name": "POV Camera",
                "role": "pov_camera",
                "resolution": (3024, 4032), # 12MP capture
                "fps": 30,
                "nominal_fx": 2450.0,
                "nominal_fy": 2450.0,
            }
        ],
        "cooling_type": "passive_pure",
        "thermal_zone_path": "/sys/class/thermal/thermal_zone1/temp",
        "stereo_baseline_nominal_mm": 0.0,
        "requires_stereo_validation": False,
        "max_temperature_warning_celsius": 42.0, # Strict for temple skin contact
    },
    "compact_glasses": {
        "name": "Compact Smart Glasses (Everyday Wearable)",
        "type": "Smart Glasses (Multimodal Wearable)",
        "cameras": [
            {
                "id": 0,
                "name": "High-Resolution POV Sensor",
                "role": "pov_camera",
                "resolution": (4032, 3024),
                "fps": 30,
                "nominal_fx": 2200.0,
                "nominal_fy": 2200.0,
                "nominal_cx": 2016.0,
                "nominal_cy": 1512.0,
                "distortion_k1": -0.08,
                "distortion_k2": 0.03,
                "distortion_k3": 0.0,
            }
        ],
        "cooling_type": "passive_pure",
        "thermal_sensor_name": "VIRTUAL-SKIN",
        "thermal_zone_path": "/sys/class/thermal/thermal_zone0/temp",
        "stereo_baseline_nominal_mm": 0.0,
        "requires_stereo_validation": False,
        "max_temperature_warning_celsius": 42.0,
    }
}

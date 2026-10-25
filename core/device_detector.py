"""
Device Detector module: Identifies target hardware (XR Headset, AR Glasses, Smart Glasses)
and binds appropriate hardware profile and calibration rules.
"""

from typing import Dict, Any, Optional
from config import DEVICE_PROFILES
from core.adb_bridge import ADBBridge


class DeviceDetector:
    def __init__(self, bridge: ADBBridge):
        self.bridge = bridge

    def detect_device(self, forced_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Detects connected hardware and returns corresponding profile.
        If forced_key is provided, uses that specific profile.
        """
        if forced_key and forced_key.lower() in DEVICE_PROFILES:
            profile = DEVICE_PROFILES[forced_key.lower()].copy()
            profile["profile_key"] = forced_key.lower()
            profile["detection_source"] = "manual_override"
            return profile

        # Read hardware fingerprints via ADB
        device_prop = self.bridge.get_property("ro.product.device").lower()
        model_prop = self.bridge.get_property("ro.product.model").lower()
        board_prop = self.bridge.get_property("ro.product.board").lower()

        combined_fingerprint = f"{device_prop} {model_prop} {board_prop}".strip()

        matched_key = "xr_headset" # Default fallback for Android XR headset
        if any(token in combined_fingerprint for token in ["waveguide", "ost", "ar_glasses"]):
            matched_key = "ar_glasses"
        elif any(token in combined_fingerprint for token in ["audio_ai", "smart_glasses"]):
            matched_key = "smart_glasses"
        elif any(token in combined_fingerprint for token in ["compact", "wearable"]):
            matched_key = "compact_glasses"
        elif any(token in combined_fingerprint for token in ["headset", "hmd", "xr_vst"]):
            matched_key = "xr_headset"

        profile = DEVICE_PROFILES[matched_key].copy()
        profile["profile_key"] = matched_key
        profile["detection_source"] = "adb_fingerprint"
        profile["fingerprint"] = combined_fingerprint or "Emulated Device (Mock)"
        return profile

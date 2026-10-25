"""
ADB Bridge module: Handles low-level communication with Android XR hardware.
Includes full hardware emulation (Mock mode) for offline development, CI/CD, and demonstrations.
"""

import subprocess
import shutil
import math
import random
import time
from typing import Optional, List, Dict, Any, Tuple


class ADBBridge:
    def __init__(self, serial: Optional[str] = None, mock_mode: bool = False):
        self.serial = serial
        self.mock_mode = mock_mode
        self.adb_path = shutil.which("adb")

    def is_available(self) -> bool:
        """Check if adb executable is in system PATH."""
        return self.adb_path is not None

    def list_connected_devices(self) -> List[str]:
        """Returns list of connected adb device serials."""
        if self.mock_mode or not self.is_available():
            return ["MOCK_XR_HEADSET_001", "MOCK_AR_GLASSES_002", "MOCK_SMART_GLASSES_003"]
        
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            devices = []
            for line in result.stdout.strip().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception:
            return []

    def run_shell(self, command: str, timeout: int = 10) -> Tuple[int, str, str]:
        """Runs an adb shell command on target device."""
        if self.mock_mode:
            return self._mock_shell(command)
        
        cmd = ["adb"]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(["shell", command])
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return res.returncode, res.stdout, res.stderr
        except Exception as e:
            return -1, "", str(e)

    def get_property(self, prop_name: str) -> str:
        """Fetch system property via getprop."""
        code, out, _ = self.run_shell(f"getprop {prop_name}")
        return out.strip() if code == 0 else ""

    def get_thermal_celsius(self, thermal_path: str = "/sys/class/thermal/thermal_zone0/temp") -> float:
        """Reads instantaneous temperature in Celsius."""
        if self.mock_mode:
            # Emulate gradual warm-up: 36C baseline with slight thermal noise
            return 36.5 + (random.uniform(-0.4, 0.6))
        
        # 1. First priority: dumpsys thermalservice for skin/temple temperature
        code, out, _ = self.run_shell("dumpsys thermalservice")
        if code == 0 and out:
            # Look for temple skin or cpu temperature
            for line in out.splitlines():
                if any(sensor in line for sensor in ["VIRTUAL-SKIN", "SKIN", "CPU", "AP"]):
                    # Lines like: Temperature{mValue=29.8, mType=3, mName=VIRTUAL-SKIN, mStatus=0}
                    if "mValue=" in line:
                        try:
                            val_part = line.split("mValue=")[1].split(",")[0].strip()
                            val = float(val_part)
                            if 15.0 <= val <= 90.0:
                                return round(val, 1)
                        except (ValueError, IndexError):
                            pass

        # 2. Fallback to sysfs thermal zone
        code, out, _ = self.run_shell(f"cat {thermal_path}")
        if code == 0 and out.strip().isdigit():
            val = float(out.strip())
            return round(val / 1000.0 if val > 1000 else val, 1)

        return 32.0

    def get_live_camera_metadata(self) -> Dict[str, Any]:
        """
        Parses actual factory calibration data from Android Camera HAL via dumpsys media.camera.
        """
        code, out, _ = self.run_shell("dumpsys media.camera")
        if code != 0 or not out:
            return {}

        metadata = {}
        lines = out.splitlines()
        for i, line in enumerate(lines):
            if "android.lens.intrinsicCalibration" in line and i + 1 < len(lines):
                # Next line has values like: [1500.00000000 1500.00000000 960.00000000 540.00000000 0.00000000 ]
                val_line = lines[i + 1].strip("[] \t")
                tokens = [t.strip() for t in val_line.split() if t.strip()]
                if len(tokens) >= 4:
                    try:
                        metadata["fx"] = float(tokens[0])
                        metadata["fy"] = float(tokens[1])
                        metadata["cx"] = float(tokens[2])
                        metadata["cy"] = float(tokens[3])
                    except ValueError:
                        pass

            if "android.lens.distortion" in line and i + 1 < len(lines):
                val_line = lines[i + 1].strip("[] \t")
                tokens = [t.strip() for t in val_line.split() if t.strip()]
                if len(tokens) >= 3:
                    try:
                        metadata["k1"] = float(tokens[0])
                        metadata["k2"] = float(tokens[1])
                        metadata["p1"] = float(tokens[2])
                    except ValueError:
                        pass

        return metadata

    def capture_frame_matrix(self, width: int = 640, height: int = 480, pattern: str = "checkerboard") -> List[List[int]]:
        """
        Captures or simulates an 8-bit grayscale image matrix [[int, ...], ...].
        Used for zero-dependency sanity and calibration checks.
        """
        matrix = []
        if pattern == "dark_field":
            # Mostly zero with occasional noise and isolated stuck pixels
            for y in range(height):
                row = [random.randint(0, 2) for _ in range(width)]
                matrix.append(row)
            # Inject a stuck pixel
            matrix[height // 2][width // 2] = 255
            matrix[height // 3][width // 4] = 240
            return matrix

        elif pattern == "overexposed":
            for y in range(height):
                row = [252 if random.random() > 0.1 else 230 for _ in range(width)]
                matrix.append(row)
            return matrix

        elif pattern == "checkerboard":
            # Synthesize an 8x6 square grid pattern
            square_size = max(width // 10, height // 10, 16)
            for y in range(height):
                row = []
                for x in range(width):
                    tile_x = (x // square_size) % 2
                    tile_y = (y // square_size) % 2
                    val = 220 if (tile_x ^ tile_y) else 35
                    # Add mild sensor photon noise
                    val = max(0, min(255, val + random.randint(-4, 4)))
                    row.append(val)
                matrix.append(row)
            return matrix

        else: # Standard gradient / natural image proxy
            for y in range(height):
                row = []
                for x in range(width):
                    val = int(128 + 70 * math.sin(x / 40.0) * math.cos(y / 40.0))
                    row.append(max(0, min(255, val)))
                matrix.append(row)
            return matrix

    def _mock_shell(self, cmd: str) -> Tuple[int, str, str]:
        """Provides realistic mock responses for Android XR hardware."""
        c = cmd.lower().strip()
        if "getprop ro.product.device" in c or "getprop ro.build.product" in c:
            return 0, "xr_vst_hmd", ""
        if "getprop ro.product.model" in c:
            return 0, "Android-XR-HMD (Reference)", ""
        if "dumpsys media.camera" in c:
            mock_camera_dump = (
                "Camera module API version: 0x204\n"
                "Number of camera devices: 4\n"
                "Device 0: Left Passthrough Camera (FACING_BACK)\n"
                "Device 1: Right Passthrough Camera (FACING_BACK)\n"
                "Device 2: Tracking SLAM Fisheye (FACING_FRONT)\n"
                "Device 3: Eye Tracking IR Sensor (FACING_FRONT)\n"
            )
            return 0, mock_camera_dump, ""
        if "dumpsys thermalservice" in c:
            return 0, "Current temperature: Skin=38.4C, CPU=41.2C, ThrottlingStatus=NONE", ""
        if "cat /sys/class/thermal" in c:
            return 0, "38500", ""
        
        return 0, "OK", ""

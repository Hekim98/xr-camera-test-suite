"""
Automated Test Suite for XR Camera Test & Calibration Harness.
Compatible with standard unittest runner and Pytest.
"""

import unittest
from config import THRESHOLDS, DEVICE_PROFILES
from core.adb_bridge import ADBBridge
from core.device_detector import DeviceDetector
from modules.sensor_sanity import SensorSanityChecker
from modules.calibration_validator import CalibrationValidator
from modules.thermal_profiler import ThermalProfiler


class TestXRCameraSuite(unittest.TestCase):

    def setUp(self):
        self.bridge = ADBBridge(mock_mode=True)
        self.detector = DeviceDetector(self.bridge)
        self.sanity_checker = SensorSanityChecker(thresholds=THRESHOLDS)
        self.calib_validator = CalibrationValidator(thresholds=THRESHOLDS)
        self.thermal_profiler = ThermalProfiler(bridge=self.bridge, thresholds=THRESHOLDS)

    def test_device_detection_profiles(self):
        """Verify all target hardware profiles are correctly defined and identifiable."""
        generic_keys = ["xr_headset", "ar_glasses", "smart_glasses", "compact_glasses"]
        # Only generic reference profiles are allowed (no product names or codenames).
        self.assertEqual(set(DEVICE_PROFILES), set(generic_keys))
        for device_key in generic_keys:
            profile = self.detector.detect_device(forced_key=device_key)
            self.assertEqual(profile["profile_key"], device_key)
            self.assertIn("cameras", profile)
            self.assertGreater(len(profile["cameras"]), 0)
            self.assertIn("cooling_type", profile)

    def test_sensor_dead_pixels_pass_and_fail(self):
        """Test dead/stuck pixel detection under pass and fail scenarios."""
        # Simulated dark frame with 2 stuck pixels (Pass <= 5)
        dark_frame = self.bridge.capture_frame_matrix(width=100, height=100, pattern="dark_field")
        res = self.sanity_checker.check_dead_pixels(dark_frame)
        self.assertEqual(res["status"], "PASS")

        # Inject 10 stuck pixels (Fail > 5)
        for i in range(10):
            dark_frame[i][i] = 255
        res_fail = self.sanity_checker.check_dead_pixels(dark_frame)
        self.assertEqual(res_fail["status"], "FAIL")
        self.assertGreater(res_fail["measured_value"], 5)

    def test_sensor_laplacian_sharpness(self):
        """Test sharpness calculation with sharp pattern vs flat/blurred field."""
        sharp_frame = self.bridge.capture_frame_matrix(width=120, height=120, pattern="checkerboard")
        res_sharp = self.sanity_checker.calculate_laplacian_sharpness(sharp_frame)
        self.assertEqual(res_sharp["status"], "PASS")
        self.assertGreaterEqual(res_sharp["measured_value"], THRESHOLDS["min_sharpness_score"])

        # Completely flat/defocused frame (variance ~ 0)
        flat_frame = [[120 for _ in range(120)] for _ in range(120)]
        res_flat = self.sanity_checker.calculate_laplacian_sharpness(flat_frame)
        self.assertEqual(res_flat["status"], "FAIL")

    def test_exposure_clipping(self):
        """Verify overexposed and underexposed dynamic range check."""
        normal_frame = self.bridge.capture_frame_matrix(width=100, height=100, pattern="checkerboard")
        res_normal = self.sanity_checker.check_exposure_clipping(normal_frame)
        self.assertEqual(res_normal["status"], "PASS")

        blown_out_frame = self.bridge.capture_frame_matrix(width=100, height=100, pattern="overexposed")
        res_blown = self.sanity_checker.check_exposure_clipping(blown_out_frame)
        self.assertEqual(res_blown["status"], "WARN")

    def test_calibration_reprojection_error(self):
        """Validate Root Mean Square (RMS) re-projection error calculation."""
        # Perfect match: RMS == 0.0 -> PASS
        measured = [(10.0, 20.0), (30.0, 40.0), (50.0, 60.0)]
        projected_perfect = [(10.0, 20.0), (30.0, 40.0), (50.0, 60.0)]
        res_pass = self.calib_validator.calculate_reprojection_error(measured, projected_perfect)
        self.assertEqual(res_pass["status"], "PASS")
        self.assertEqual(res_pass["measured_value"], 0.0)

        # Distorted/mismatched points: RMS > 1.0 -> FAIL
        projected_bad = [(12.0, 22.0), (32.0, 42.0), (52.0, 62.0)]
        res_fail = self.calib_validator.calculate_reprojection_error(measured, projected_bad)
        self.assertEqual(res_fail["status"], "FAIL")
        self.assertGreater(res_fail["measured_value"], 1.0)

    def test_stereo_baseline_and_epipolar_validation(self):
        """Verify stereo baseline and epipolar validation for a stereo VST headset."""
        good_extrinsics = {"baseline_mm": 63.85, "vertical_disparity_px": 0.25}
        res_good = self.calib_validator.verify_stereo_alignment(good_extrinsics)
        self.assertEqual(res_good["status"], "PASS")

        bad_extrinsics = {"baseline_mm": 60.0, "vertical_disparity_px": 1.45}
        res_bad = self.calib_validator.verify_stereo_alignment(bad_extrinsics)
        self.assertEqual(res_bad["status"], "FAIL")

    def test_thermal_profiler_execution(self):
        """Ensure thermal and frame stability profiler samples telemetry correctly."""
        profile = DEVICE_PROFILES["smart_glasses"]
        res = self.thermal_profiler.run_thermal_stress_test(
            device_profile=profile,
            duration_seconds=2,
            target_fps=30.0
        )
        self.assertIn("category", res)
        self.assertIn("telemetry_timeline", res)
        self.assertGreater(len(res["telemetry_timeline"]), 0)
        self.assertIn("peak_temperature", res["tests"])
        self.assertIn("frame_drops", res["tests"])


if __name__ == "__main__":
    unittest.main()

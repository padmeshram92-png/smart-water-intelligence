import unittest
from detector import Reading, detect_issue

class DetectorTests(unittest.TestCase):
    def test_normal_reading(self):
        r = Reading("normal", 0.3, 55, 10, 20, 18)
        self.assertEqual(detect_issue(r).status, "Normal")

    def test_continuous_flow_alert(self):
        r = Reading("continuous_flow", 1.4, 60, 45, 30, 55)
        result = detect_issue(r)
        self.assertEqual(result.alert_type, "possible_continuous_flow")
        self.assertEqual(result.status, "Alert")

    def test_tank_overflow_risk(self):
        r = Reading("tank_overflow", 2.0, 98, 8, 15, 16)
        self.assertEqual(detect_issue(r).alert_type, "tank_overflow_risk")

    def test_usage_spike(self):
        r = Reading("usage_spike", 0.4, 70, 20, 25, 65)
        self.assertEqual(detect_issue(r).alert_type, "unusual_consumption")

    def test_invalid_tank_level(self):
        r = Reading("normal", 0.3, 120, 10, 20, 18)
        self.assertEqual(detect_issue(r).alert_type, "data_error")

if __name__ == "__main__":
    unittest.main(verbosity=2)

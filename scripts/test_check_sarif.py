import unittest
from check_sarif import count_errors

class SarifTests(unittest.TestCase):
    def test_rule_level_and_override(self):
        rule = {"id": "x", "defaultConfiguration": {"level": "error"}}
        report = {"runs": [{"tool": {"driver": {"rules": [rule]}}, "results": [
            {"ruleId": "x"}, {"ruleIndex": 0}, {"ruleId": "x", "level": "warning"}]}]}
        self.assertEqual(count_errors(report), 2)
    def test_multiple_runs_and_missing_report(self):
        self.assertEqual(count_errors({"runs": [{"results": [{"level": "error"}]}, {"results": [{"level": "error"}]}]}), 2)
        with self.assertRaises(ValueError): count_errors({})
        with self.assertRaises(ValueError): count_errors({"runs": []})

if __name__ == "__main__": unittest.main()

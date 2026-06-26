import unittest

try:
    import calamus_ui as ui
except ModuleNotFoundError as exc:
    if exc.name == "gi":
        ui = None
    else:
        raise


@unittest.skipIf(ui is None, "PyGObject not available in test environment")
class UiWiringTests(unittest.TestCase):
    def test_shortcut_conflict_helper(self):
        self.assertEqual(ui.shortcut_conflicts((("<Control>N", object()), ("F1", object()))), {})
        self.assertEqual(ui.shortcut_conflicts((("F1", object()), ("F1", object()))), {"F1": 2})


if __name__ == "__main__":
    unittest.main()

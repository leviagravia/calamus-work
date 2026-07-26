import unittest

from calamus_modal_dialog import destroy_modal, run_modal


class _Dialog:
    def __init__(self, response=7):
        self.response = response
        self.events = []

    def run(self):
        self.events.append("run")
        return self.response

    def destroy(self):
        self.events.append("destroy")


class ModalDialogBoundaryTests(unittest.TestCase):
    def test_run_modal_returns_typed_integer_response(self):
        dialog = _Dialog(response=12)
        self.assertEqual(run_modal(dialog), 12)
        self.assertEqual(dialog.events, ["run"])

    def test_destroy_modal_delegates_to_dialog_owner(self):
        dialog = _Dialog()
        destroy_modal(dialog)
        self.assertEqual(dialog.events, ["destroy"])

    def test_missing_run_or_destroy_fails_closed(self):
        with self.assertRaises(TypeError):
            run_modal(object())
        with self.assertRaises(TypeError):
            destroy_modal(object())


if __name__ == "__main__":
    unittest.main()

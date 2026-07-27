import unittest

from calamus_modal_dialog import ModalSession, destroy_modal, run_modal


class _Dialog:
    def __init__(self, response=7):
        self.response_value = response
        self.events = []

    def run(self):
        self.events.append("run")
        return self.response_value

    def hide(self):
        self.events.append("hide")

    def destroy(self):
        self.events.append("destroy")


class ModalDialogBoundaryTests(unittest.TestCase):
    def test_run_modal_returns_typed_response_and_hides_before_result_use(self):
        dialog = _Dialog(response=12)
        self.assertEqual(run_modal(dialog), 12)
        self.assertEqual(dialog.events, ["run", "hide"])

    def test_destroy_modal_hides_then_delegates_to_dialog_owner(self):
        dialog = _Dialog()
        destroy_modal(dialog)
        self.assertEqual(dialog.events, ["hide", "destroy"])

    def test_session_owns_sources_response_and_teardown_order(self):
        dialog = _Dialog(response=9)
        removed = []
        session = ModalSession(dialog)
        session.register_source(11, lambda source_id: removed.append(source_id))
        session.register_source(12, lambda source_id: removed.append(source_id))
        self.assertEqual(session.source_count, 2)
        self.assertEqual(session.run(), 9)
        self.assertEqual(session.response, 9)
        self.assertEqual(dialog.events, ["run", "hide"])
        session.close()
        self.assertEqual(removed, [12, 11])
        self.assertEqual(dialog.events, ["run", "hide", "hide", "destroy"])
        self.assertTrue(session.closed)
        self.assertEqual(session.source_count, 0)
        session.close()  # controlled idempotent session close
        self.assertEqual(removed, [12, 11])

    def test_context_manager_closes_after_result_is_copied(self):
        dialog = _Dialog(response=3)
        with ModalSession(dialog) as session:
            response = session.run()
            self.assertFalse(session.closed)
            self.assertEqual(response, 3)
        self.assertTrue(session.closed)
        self.assertEqual(dialog.events[-2:], ["hide", "destroy"])

    def test_missing_methods_and_invalid_sources_fail_closed(self):
        with self.assertRaises(TypeError):
            run_modal(object())
        with self.assertRaises(TypeError):
            destroy_modal(object())
        session = ModalSession(_Dialog())
        with self.assertRaises(ValueError):
            session.register_source(0, lambda _source_id: None)
        with self.assertRaises(TypeError):
            session.register_source(1, object())
        session.close()
        with self.assertRaises(RuntimeError):
            session.run()
        with self.assertRaises(RuntimeError):
            session.register_source(2, lambda _source_id: None)


if __name__ == "__main__":
    unittest.main()

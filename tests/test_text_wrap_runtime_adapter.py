import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / "calamus" / "calamus_editor.py"


def _compiled_adapter(namespace):
    source = EDITOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "apply_text_wrap_policy":
            isolated = copy.deepcopy(node)
            module = ast.Module(body=[isolated], type_ignores=[])
            ast.fix_missing_locations(module)
            scope = dict(namespace)
            exec(compile(module, str(EDITOR), "exec"), scope)
            return scope[node.name]
    raise AssertionError("apply_text_wrap_policy not found")


class _WrapMode:
    WORD_CHAR = "word-char"
    NONE = "none"


class _PolicyType:
    AUTOMATIC = "automatic"
    NEVER = "never"


class _Gtk:
    WrapMode = _WrapMode
    PolicyType = _PolicyType


class _Adjustment:
    def __init__(self, lower=0, value=73):
        self.lower = lower
        self.value = value

    def get_lower(self):
        return self.lower

    def set_value(self, value):
        self.value = value


class _Text:
    def __init__(self):
        self.wrap_mode = None
        self.resize_count = 0

    def set_wrap_mode(self, mode):
        self.wrap_mode = mode

    def queue_resize(self):
        self.resize_count += 1


class _Scroller:
    def __init__(self):
        self.policy = None
        self.adjustment = _Adjustment()
        self.resize_count = 0

    def set_policy(self, horizontal, vertical):
        self.policy = (horizontal, vertical)

    def get_hadjustment(self):
        return self.adjustment

    def queue_resize(self):
        self.resize_count += 1


class TextWrapRuntimeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.apply = _compiled_adapter({"Gtk": _Gtk})

    def test_enable_wrap_uses_word_char_and_automatic_viewport_policy(self):
        text = _Text()
        scroller = _Scroller()
        self.assertTrue(self.apply(text, scroller, True))
        self.assertEqual(text.wrap_mode, _WrapMode.WORD_CHAR)
        self.assertEqual(scroller.policy, (_PolicyType.AUTOMATIC, _PolicyType.AUTOMATIC))
        self.assertEqual(scroller.adjustment.value, scroller.adjustment.lower)
        self.assertEqual(text.resize_count, 1)
        self.assertEqual(scroller.resize_count, 1)

    def test_disable_wrap_uses_none_and_preserves_horizontal_position(self):
        text = _Text()
        scroller = _Scroller()
        self.assertFalse(self.apply(text, scroller, False))
        self.assertEqual(text.wrap_mode, _WrapMode.NONE)
        self.assertEqual(scroller.policy, (_PolicyType.AUTOMATIC, _PolicyType.AUTOMATIC))
        self.assertEqual(scroller.adjustment.value, 73)

    def test_rejects_non_boolean_state(self):
        with self.assertRaises(TypeError):
            self.apply(_Text(), _Scroller(), 1)


if __name__ == "__main__":
    unittest.main()

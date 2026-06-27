import unittest

from calamus_navigation import clamp_line_number, line_to_buffer_index


class NavigationHelperTests(unittest.TestCase):
    def test_clamp_line_number_preserves_valid_line(self):
        self.assertEqual(clamp_line_number(1, 10), 1)
        self.assertEqual(clamp_line_number(7, 10), 7)
        self.assertEqual(clamp_line_number(10, 10), 10)

    def test_clamp_line_number_rejects_lower_bound(self):
        self.assertEqual(clamp_line_number(0, 10), 1)
        self.assertEqual(clamp_line_number(-5, 10), 1)

    def test_clamp_line_number_rejects_upper_bound(self):
        self.assertEqual(clamp_line_number(99, 10), 10)

    def test_clamp_line_number_handles_bad_total_lines(self):
        self.assertEqual(clamp_line_number(7, 0), 1)
        self.assertEqual(clamp_line_number(7, -4), 1)
        self.assertEqual(clamp_line_number(7, None), 1)

    def test_clamp_line_number_handles_bad_requested_line(self):
        self.assertEqual(clamp_line_number(None, 10), 1)
        self.assertEqual(clamp_line_number("bad", 10), 1)

    def test_line_to_buffer_index_uses_zero_based_index(self):
        self.assertEqual(line_to_buffer_index(1, 10), 0)
        self.assertEqual(line_to_buffer_index(10, 10), 9)

    def test_line_to_buffer_index_clamps_before_converting(self):
        self.assertEqual(line_to_buffer_index(0, 10), 0)
        self.assertEqual(line_to_buffer_index(99, 10), 9)
        self.assertEqual(line_to_buffer_index(2, 0), 0)


if __name__ == "__main__":
    unittest.main()

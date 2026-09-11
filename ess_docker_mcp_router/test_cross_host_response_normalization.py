import unittest

from normalized_replay import normalize_tool_response


class CrossHostResponseNormalizationTests(unittest.TestCase):
    def test_only_tool_call_duration_prefix_is_removed(self):
        a = 'Tool call took: 3.475567752s\n{"paper_id":"1802.09555v2","title":"Involutive categories"}\n'
        b = 'Tool call took: 1.829770029s\n{"paper_id":"1802.09555v2","title":"Involutive categories"}\n'
        self.assertEqual(normalize_tool_response(a), normalize_tool_response(b))
        self.assertEqual(
            '{"paper_id":"1802.09555v2","title":"Involutive categories"}\n',
            normalize_tool_response(a),
        )

    def test_professional_content_difference_is_not_normalized_away(self):
        a = 'Tool call took: 1.0s\n{"paper_id":"A","title":"Alpha"}\n'
        b = 'Tool call took: 9.0s\n{"paper_id":"A","title":"Beta"}\n'
        self.assertNotEqual(normalize_tool_response(a), normalize_tool_response(b))

    def test_non_timing_first_line_is_preserved(self):
        text = 'Tool result follows\n{"paper_id":"A"}\n'
        self.assertEqual(text, normalize_tool_response(text))


if __name__ == '__main__':
    unittest.main()

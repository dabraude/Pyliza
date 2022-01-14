import unittest
from hypothesis import given

from . import pyliza_strategies as liza_st
from pyliza.transformation import DecompositionRule


class DecompositionTestCase(unittest.TestCase):
    @given(liza_st.valid_decomposition())
    def test_decompose(self, eg):
        """Decomposition will correctly decompose a phrase."""
        pattern, decomposed_phrase, phrase = eg
        rule = DecompositionRule(pattern)
        decomposed = rule.decompose(phrase)
        self.assertEqual(len(decomposed_phrase), len(decomposed))
        for real, dec in zip(decomposed_phrase, decomposed):
            self.assertEqual(real, dec)

    @given(liza_st.invalid_decomposition())
    def test_no_match_decompose(self, eg):
        """Decomposition will return None if the phrase doesn't work."""
        pattern, phrase = eg
        rule = DecompositionRule(pattern)
        self.assertIsNone(rule.decompose(phrase))

    def test_bad_patterns(self):
        """Check against some invalid inputs."""
        self.assertRaises(ValueError, DecompositionRule, None)
        self.assertRaises(ValueError, DecompositionRule, [])
        self.assertRaises(ValueError, DecompositionRule, [None])
        self.assertRaises(ValueError, DecompositionRule, [""])
        self.assertRaises(ValueError, DecompositionRule, [0.99])
        self.assertRaises(ValueError, DecompositionRule, [{0.99}])
        self.assertRaises(ValueError, DecompositionRule, [{None}])

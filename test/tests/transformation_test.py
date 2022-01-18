import unittest
from hypothesis import given, example

from . import pyliza_strategies as liza_st
from pyliza.transformation import DecompositionRule
from pyliza.processing import ProcessingWord as PW
from pyliza.processing import ProcessingPhrase as PPhrase


class DecompositionTestCase(unittest.TestCase):
    @given(liza_st.valid_decomposition())
    @example(([0], [[]], PPhrase([])))
    @example(([1, PW("A")], [[PW("A")], [PW("A")]], PPhrase([PW("A"), PW("A")])))
    @example(([1], [[PW("A")]], PPhrase([PW("A")])))
    @example(([0, PW("A")], [[], [PW("A")]], PPhrase([PW("A")])))
    def test_matching(self, eg):
        """Decomposition will correctly decompose a phrase."""
        pattern, decomposed_phrase, phrase = eg
        rule = DecompositionRule(pattern)
        decomposed = rule.decompose(phrase)
        self.assertEqual(len(decomposed_phrase), len(decomposed))
        for real, dec in zip(decomposed_phrase, decomposed):
            self.assertEqual(real, dec)

    @given(liza_st.invalid_decomposition())
    def test_non_match(self, eg):
        """Decomposition will return None if the phrase doesn't match the pattern."""
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
        self.assertRaises(ValueError, DecompositionRule, [{""}])

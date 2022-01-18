import unittest
from hypothesis import strategies as st
from typing import Tuple

from hypothesis import given


from .. import utils
from .. import pyliza_strategies as liza_st

from pyliza.processing import ProcessingWord
from pyliza.transformation import DecompositionPattern_t
from pyliza.rule_parsing import DecompositionParser


def word_to_string(word: ProcessingWord):
    if word.word is None:
        assert len(word.tags) == 1
        return f"(/{sorted(word.tags)[0]})"
    return word.word


@st.composite
def decompsition_string(draw: st.DrawFn) -> Tuple[str, DecompositionPattern_t]:
    pattern, _ = draw(liza_st.decomposition_pattern())
    string_parts = []
    for elem in pattern:
        if isinstance(elem, set):
            string_parts.append(
                "(* " + " ".join([word_to_string(w) for w in sorted(elem)]) + ")"
            )
            continue
        if isinstance(elem, int):
            string_parts.append(str(elem))
            continue

        string_parts.append(word_to_string(elem))
    return " ".join(string_parts), pattern


class DecompositionParserTestCase(unittest.TestCase):
    @given(decompsition_string())
    def test_parsing(self, eg):
        """Test parsing generates the correct patterns."""
        string, pattern = eg
        parsed_rule = DecompositionParser.parse(string)
        self.assertEqual(
            pattern,
            parsed_rule.pattern,
            msg=f"pattern failed to parse when string is '{string}'",
        )

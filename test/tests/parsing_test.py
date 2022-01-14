import unittest
from hypothesis import strategies as st
from typing import Tuple

from hypothesis import given

from . import utils
from . import pyliza_strategies as liza_st

from pyliza.transformation import DecompositionPattern_t
from pyliza.rule_parsing import DecompositionParser


@st.composite
def decompsition_string(draw: st.DrawFn) -> Tuple[str, DecompositionPattern_t]:
    pattern, _ = draw(liza_st.decomposition_pattern())
    string_parts = []
    for elem in pattern:
        if isinstance(elem, set):
            string_parts.append("(* " + " ".join([w for w in sorted(elem)]) + ")")
        else:
            string_parts.append(str(elem))

    return " ".join(string_parts), pattern


class DecompositionParserTestCase(unittest.TestCase):
    @given(decompsition_string())
    def test_parsing(self, eg):
        """Test parsing generates the correct patterns."""
        string, pattern = eg
        parsed_rule = DecompositionParser.parse(string)
        self.assertEqual(pattern, parsed_rule.pattern)

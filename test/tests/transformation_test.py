import pathlib
import sys
import re
import unittest
from typing import Tuple, List
from hypothesis import given, strategies as st

sys.path.insert(0, str(pathlib.Path(__file__).parent / "../.."))
import pyliza
from pyliza.processing import ProcessingPhrase, ProcessingWord
from pyliza.transformation import (
    DecompositionRule,
    ReassemblyRule,
    DecompositionPattern_t,
)


@st.composite
def decomposition_pattern_strat(draw: st.DrawFn) -> DecompositionPattern_t:
    """Make a valid decomposition pattern."""
    int_strat = st.integers(min_value=0, max_value=10)
    str_strat = st.from_regex(r"\S+").filter(lambda s: re.match(r"\(/", s) is None)
    # tag_strat = st.from_regex(r"\(/\S+\)")
    set_strat = st.sets(str_strat, min_size=1)

    initial_pattern = draw(
        st.lists(st.one_of(int_strat, str_strat, set_strat), min_size=1)
    )
    pattern = initial_pattern[:1]
    for element in initial_pattern[1:]:
        if element != 0 or pattern[-1] != 0:
            pattern.append(element)
    return pattern


@st.composite
def decomposition_strat(
    draw: st.DrawFn,
) -> Tuple[DecompositionPattern_t, List[List[ProcessingWord]]]:
    """Make a decomposition and a phrase that should work."""
    pattern = draw(decomposition_pattern_strat())
    used_words = set()
    for element in pattern:
        if isinstance(element, str):
            used_words.add(element)
        if isinstance(element, set):
            used_words.update(element)

    new_words_strat = (
        st.from_regex(r"\S+")
        .filter(lambda s: re.match(r"\(/", s) is None)
        .filter(lambda s: s not in used_words)
        .map(ProcessingWord)
    )

    decomposed_phrase = []
    for element in pattern:
        if element == 0:
            nwords = draw(st.integers(min_value=0, max_value=10))
            decomposed_phrase.append(
                draw(st.lists(new_words_strat, min_size=nwords, max_size=nwords))
            )
        elif isinstance(element, int):
            decomposed_phrase.append(
                draw(st.lists(new_words_strat, min_size=element, max_size=element))
            )
        elif isinstance(element, str):
            decomposed_phrase.append([element])
        elif isinstance(element, set):
            decomposed_phrase.append([draw(st.sampled_from(sorted(element)))])

    phrase = ProcessingPhrase([w for d in decomposed_phrase for w in d])

    return pattern, decomposed_phrase, phrase


class DecompositionTestCase(unittest.TestCase):
    @given(decomposition_strat())
    def test_decompose(self, eg):
        pattern, decomposed_phrase, phrase = eg
        rule = DecompositionRule(pattern)
        decomposed = rule.decompose(phrase)
        self.assertEqual(len(decomposed_phrase), len(decomposed))
        for real, dec in zip(decomposed_phrase, decomposed):
            self.assertEqual(real, dec)

import pathlib
import sys
import re
import unittest
from typing import Tuple, List
from hypothesis import assume, given, strategies as st

sys.path.insert(0, str(pathlib.Path(__file__).parent / "../.."))
import pyliza
from pyliza.processing import ProcessingPhrase, ProcessingWord
from pyliza.transformation import (
    DecompositionRule,
    ReassemblyRule,
    DecompositionPattern_t,
)


def new_words_strat(used_words=None, return_processing=False):
    if used_words is None:
        used_words = []
    strat = (
        st.from_regex(r"\w+", fullmatch=True)
        .filter(lambda s: re.match(r"\(/", s) is None)
        .filter(lambda s: s not in used_words)
    )
    if return_processing:
        return strat.map(ProcessingWord)
    return strat


@st.composite
def decomposition_pattern_strat(draw: st.DrawFn) -> DecompositionPattern_t:
    """Make a valid decomposition pattern."""
    int_strat = st.integers(min_value=0, max_value=10)
    str_strat = new_words_strat()
    tag_strat = new_words_strat()
    set_strat = st.sets(new_words_strat(), min_size=1)

    initial_pattern = draw(
        st.lists(st.one_of(int_strat, str_strat, tag_strat, set_strat), min_size=1)
    )
    pattern = []
    int_pattern = []
    # cannot have more than 1 zero in a section of integers otherwise it would
    # be ambigious
    for element in initial_pattern:
        if isinstance(element, int):
            int_pattern.append(element)
        else:
            while int_pattern.count(0) > 1:
                int_pattern.remove(0)
            pattern.extend(int_pattern)
            int_pattern = []
            pattern.append(element)
    while int_pattern.count(0) > 1:
        int_pattern.remove(0)
    pattern.extend(int_pattern)

    used_words = set()
    for element in pattern:
        if isinstance(element, str):
            used_words.add(element)
        if isinstance(element, set):
            used_words.update(element)

    return pattern, used_words


@st.composite
def valid_decomposition_strat(
    draw: st.DrawFn,
) -> Tuple[DecompositionPattern_t, List[List[ProcessingWord]], ProcessingPhrase]:
    """Make a decomposition and a phrase that should work."""
    pattern, used_words = draw(decomposition_pattern_strat())

    nw_strat = new_words_strat(used_words, True)
    decomposed_phrase = []
    for element in pattern:
        if element == 0:
            nwords = draw(st.integers(min_value=0, max_value=10))
            decomposed_phrase.append(
                draw(st.lists(nw_strat, min_size=nwords, max_size=nwords))
            )
        elif isinstance(element, int):
            decomposed_phrase.append(
                draw(st.lists(nw_strat, min_size=element, max_size=element))
            )
        elif isinstance(element, str):
            decomposed_phrase.append([ProcessingWord(element)])
        elif isinstance(element, set):
            decomposed_phrase.append(
                [ProcessingWord(draw(st.sampled_from(sorted(element))))]
            )

    phrase = ProcessingPhrase([w for d in decomposed_phrase for w in d])

    return pattern, decomposed_phrase, phrase


@st.composite
def invalid_decomposition_strat(
    draw: st.DrawFn,
) -> Tuple[DecompositionPattern_t, ProcessingPhrase]:
    """Make a decomposition and a phrase that should work."""
    pattern, used_words = draw(decomposition_pattern_strat())
    assume(pattern != [0])  # match anything pattern
    nw_strat = new_words_strat(used_words, True)
    decomposed_phrase = []
    for element in pattern:
        if element == 0:
            continue
        elif isinstance(element, int):
            too_small = draw(st.integers(min_value=1, max_value=element))
            size = element - too_small
            decomposed_phrase.append(
                draw(st.lists(nw_strat, min_size=size, max_size=size))
            )
        elif isinstance(element, str) or isinstance(element, set):
            decomposed_phrase.append([draw(nw_strat)])

    phrase = ProcessingPhrase([w for d in decomposed_phrase for w in d])
    return pattern, phrase


class DecompositionTestCase(unittest.TestCase):
    @given(valid_decomposition_strat())
    def test_decompose(self, eg):
        """Decomposition will correctly decompose a phrase."""
        pattern, decomposed_phrase, phrase = eg
        rule = DecompositionRule(pattern)
        decomposed = rule.decompose(phrase)
        self.assertEqual(len(decomposed_phrase), len(decomposed))
        for real, dec in zip(decomposed_phrase, decomposed):
            self.assertEqual(real, dec)

    @given(invalid_decomposition_strat())
    def test_no_match_decompose(self, eg):
        """Decomposition will return None if the phrase doesn't work."""
        pattern, phrase = eg
        rule = DecompositionRule(pattern)
        self.assertIsNone(rule.decompose(phrase))

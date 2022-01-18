import re
from typing import Tuple, List, Set
from hypothesis import assume, strategies as st

from . import utils
from pyliza.processing import ProcessingPhrase, ProcessingWord
from pyliza.transformation import DecompositionPattern_t


@st.composite
def new_words(draw: st.DrawFn, used_words=None):
    if used_words is None:
        used_words = set()
    word = draw(
        st.from_regex(r"[a-zA-Z]+", fullmatch=True).filter(
            lambda s: s not in used_words | {"NONE", "MEMORY"}
        )
    )
    return ProcessingWord(word)


@st.composite
def tag_words(draw: st.DrawFn, used_words=None):
    word = draw(new_words(used_words))
    return ProcessingWord(None, {word.word})


@st.composite
def decomposition_pattern(draw: st.DrawFn) -> Tuple[DecompositionPattern_t, Set[str]]:
    """Make a valid decomposition pattern."""
    int_strat = st.integers(min_value=0, max_value=10)
    str_strat = new_words()
    tag_strat = tag_words()
    set_strat = st.sets(new_words(), min_size=1)

    initial_pattern = draw(
        st.lists(st.one_of(int_strat, str_strat, tag_strat, set_strat), min_size=1)
    )
    pattern = []
    int_pattern = []
    used_words = set()

    # cannot have more than 1 zero in a section of integers otherwise it would
    # be ambigious
    for element in initial_pattern:
        if isinstance(element, int):
            int_pattern.append(element)
            continue

        while int_pattern.count(0) > 1:
            int_pattern.remove(0)
        pattern.extend(int_pattern)
        int_pattern = []
        pattern.append(element)
        if isinstance(element, str):
            used_words.add(element.word)
        if isinstance(element, set):
            for w in element:
                used_words.add(w.word)

    while int_pattern.count(0) > 1:
        int_pattern.remove(0)
    pattern.extend(int_pattern)

    return pattern, used_words


@st.composite
def valid_decomposition(
    draw: st.DrawFn,
) -> Tuple[DecompositionPattern_t, List[List[ProcessingWord]], ProcessingPhrase]:
    """Make a decomposition and a phrase that should work."""
    pattern, used_words = draw(decomposition_pattern())

    nw_strat = new_words(used_words)
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
        elif isinstance(element, ProcessingWord):
            decomposed_phrase.append([element])
        elif isinstance(element, set):
            decomposed_phrase.append([draw(st.sampled_from(sorted(element)))])

    phrase = ProcessingPhrase([w for d in decomposed_phrase for w in d])

    return pattern, decomposed_phrase, phrase


@st.composite
def invalid_decomposition(
    draw: st.DrawFn,
) -> Tuple[DecompositionPattern_t, ProcessingPhrase]:
    """Make a decomposition and a phrase that should work."""
    pattern, used_words = draw(decomposition_pattern())
    assume(pattern != [0])  # match anything pattern
    nw_strat = new_words(used_words)
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

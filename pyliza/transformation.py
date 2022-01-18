from asyncore import read
import dataclasses
import logging
import typing

from .processing import ProcessingPhrase, ProcessingWord, WordMatch_t

DecompositionPattern_t = typing.List[typing.Union[int, WordMatch_t]]
DecomposedPhrase_t = typing.List[typing.List[ProcessingWord]]


class DecompositionRule:
    _log = logging.getLogger("decompose")

    def __init__(self, decompostion_pattern: DecompositionPattern_t) -> None:
        if not decompostion_pattern:
            raise ValueError("decomposition needs at least one part")
        self._validate_pattern(decompostion_pattern)
        self._pattern = decompostion_pattern

    def _validate_pattern(self, pattern) -> None:
        """Check the pattern is valid"""
        type_msg = "decomposition patterns consists only of int, ProcessingWord, or set(ProcessingWord), found {}"
        blank_msg = "decomposition patterns cannot have blank strings"
        for part in pattern:
            if isinstance(part, int):
                continue
            elif isinstance(part, ProcessingWord):
                if not part:
                    raise ValueError(blank_msg)
            elif isinstance(part, set):
                for pp in part:
                    if not isinstance(pp, ProcessingWord):
                        raise ValueError(type_msg.format(type(pp)))
                    if not pp:
                        raise ValueError(blank_msg)
            else:
                raise ValueError(type_msg.format(type(part)))

    @property
    def pattern(self) -> DecompositionPattern_t:
        return self._pattern

    def decompose(
        self, phrase: ProcessingPhrase
    ) -> typing.Union[None, DecomposedPhrase_t]:
        """Attempt to decompose the user input, return None if cannot."""
        if not isinstance(phrase, ProcessingPhrase):
            raise ValueError("phrase is not a ProcessingPhrase")
        # print()
        # print()
        # print("phrase", phrase)
        # print("pattern", self._pattern)
        decomposed_phrase = self._decompose_from(phrase, 0, self._pattern[:], [])
        if decomposed_phrase is None:
            return None
        self._log.debug(
            f"matched decomposition rule: {self}\n\tphrase is now: "
            + " | ".join([f"{d}" for d in decomposed_phrase])
        )
        return decomposed_phrase

    def _decompose_from(
        self,
        phrase: ProcessingPhrase,
        pos: int,
        remaining_pattern: DecompositionPattern_t,
        decomposed: DecomposedPhrase_t,
    ) -> typing.Union[None, DecomposedPhrase_t]:
        # print()
        # print("pos", pos, "remain", remaining_pattern, "decomposed", decomposed)
        if not remaining_pattern:
            return None
        next_requirement = remaining_pattern.pop(0)
        part, new_pos, rest_decomposed = self._decompose_next(
            phrase, pos, next_requirement, remaining_pattern
        )
        # print("part", part, "new_pos", new_pos, "rest", rest_decomposed)
        if part is None:
            return None
        decomposed.append(part)
        if rest_decomposed is not None:
            # print(decomposed)
            # print("return", decomposed + rest_decomposed)
            return decomposed + rest_decomposed
        if not remaining_pattern and new_pos == len(phrase):
            return decomposed
        return self._decompose_from(phrase, new_pos, remaining_pattern, decomposed)

    def _decompose_next(self, phrase, pos, next_part, remaining_pattern):
        if next_part == 0:
            return self._decompose_zero(phrase, pos, remaining_pattern)
        if isinstance(next_part, int):
            return self._decompose_int(phrase, pos, next_part)
        return self._decompose_word(phrase, pos, next_part)

    def _decompose_zero(
        self,
        phrase: ProcessingPhrase,
        pos: int,
        remaining_pattern: DecompositionPattern_t,
    ):
        # if this is handled as a special case then if it falls off then end
        # if it failed to match
        if not remaining_pattern:
            return phrase[pos:], len(phrase), None

        for end_of_zero in range(pos, len(phrase)):
            # non-greedy match
            rest_decomposed = self._decompose_from(
                phrase, end_of_zero, remaining_pattern[:], []
            )
            if rest_decomposed is not None:
                return phrase[pos:end_of_zero], len(phrase), rest_decomposed
        return None, None, None

    def _decompose_int(self, phrase: ProcessingPhrase, pos: int, num_words: int):
        if pos + num_words > len(phrase):
            return None, None, None
        return phrase[pos : pos + num_words], pos + num_words, None

    def _decompose_word(
        self,
        phrase: ProcessingPhrase,
        pos: int,
        key_word: ProcessingWord,
    ):
        if pos >= len(phrase):
            return None, None, None
        if not phrase[pos].matches(key_word):
            return None, None, None
        part = [phrase[pos]]
        return part, pos + 1, None

    def __str__(self):
        return " ".join(f"{pt}" for pt in self._pattern)


class ReassemblyRule:
    def __init__(self, reassembly_parts, link):
        self._parts = reassembly_parts
        self._link = link

    def __str__(self) -> str:
        ret = ""
        if self._parts is not None:
            ret = " ".join([f"{p}" for p in self._parts])
            if self._link is not None:
                ret += f" & link to '{self._link}'"
        return ret

    def apply(self, decomposed_phrase):
        if self._parts is None:
            new_phrase = [p for d in decomposed_phrase for p in d]
            return self._link, ProcessingPhrase(new_phrase)

        new_phrase = []
        for part in self._parts:
            if isinstance(part, int):
                new_phrase.extend(decomposed_phrase[part - 1])
            else:
                new_phrase.extend(part)
        return self._link, ProcessingPhrase(new_phrase)


@dataclasses.dataclass
class TransformRule:
    decompose: DecompositionRule
    reassemble: typing.Iterable[ReassemblyRule]
    _reassemble_idx: int = dataclasses.field(init=False)
    _log: logging.Logger = dataclasses.field(init=False)

    def __post_init__(self):
        self._reassemble_idx = 0
        self._log = logging.getLogger("transform_rule")

    def get_reassemble(self):
        res = self.reassemble[self._reassemble_idx]
        self._reassemble_idx = (self._reassemble_idx + 1) % len(self.reassemble)
        return res

    def apply(self, phrase):
        self._log.debug(
            f"attempting to match against decomposition rule: {self.decompose}"
        )
        decomposed = self.decompose.decompose(phrase)
        if decomposed is None:
            return None, None

        reassembly = self.get_reassemble()
        linked_rule, phrase = reassembly.apply(decomposed)
        self._log.debug(
            f"applied reassembly rule: {reassembly}\n\tphrase is now: {phrase}"
        )
        if linked_rule:
            self._log.debug(f"reassembly rule linked to: {linked_rule}")
        return linked_rule, phrase

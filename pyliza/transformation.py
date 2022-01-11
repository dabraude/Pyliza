import dataclasses
from re import L
import typing

from .processing import ProcessingPhrase, WordMatch_t


class DecompositionRule:
    def __init__(self, decompostion_parts: typing.List[typing.Union[int, WordMatch_t]]):
        if not decompostion_parts:
            raise ValueError("decomposition needs at least one part")
        self._parts = decompostion_parts

    def match(self, phrase: ProcessingPhrase) -> typing.Union[None, typing.List[str]]:
        """Attempt to decompose the user input, return None if cannot."""
        match_part, *remaining_parts = self._parts
        decomposed = [[]]
        for word in phrase:
            if isinstance(match_part, int):
                match_part = self._match_int(
                    word, match_part, remaining_parts, decomposed
                )
            else:
                match_part = self._match_WordMatch_t(
                    word, match_part, remaining_parts, decomposed
                )
            if match_part is None:
                break
        if len(decomposed) == len(self._parts):
            return decomposed
        return None

    def _match_int(self, word, match_part, remaining_parts, decomposed):
        if match_part == 0:
            return self._match_0(word, remaining_parts, decomposed)

        decomposed[-1].append(word)
        match_part -= 1
        if match_part == 0:
            if remaining_parts:
                return remaining_parts.pop(0)
            return None
        return match_part

    def _match_0(self, word, remaining_parts, decomposed):
        if not remaining_parts:
            decomposed[-1].append(word)
            return 0
        next_part = remaining_parts[0]

        if word.matches(next_part):
            decomposed.append([word])
            remaining_parts.pop(0)
            if remaining_parts:
                decomposed.append([])
                return remaining_parts.pop(0)
            return None

        decomposed[-1].append(word)
        return 0

    def _match_WordMatch_t(self, word, match_part, remaining_parts, decomposed):
        if word.matches(match_part):
            decomposed.append([word])
            if remaining_parts:
                match_part = remaining_parts.pop(0)
                if isinstance(match_part, int):
                    decomposed.append([])
            return match_part
        return None


class ReassemblyRule:
    def __init__(self):
        pass


@dataclasses.dataclass
class TransformRule:
    decompose: DecompositionRule
    reassemble: typing.Iterable[ReassemblyRule]

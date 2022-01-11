import dataclasses
import logging
import typing

from .processing import ProcessingPhrase, WordMatch_t


class DecompositionRule:
    _log = logging.getLogger("decompose")

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
            self._log.debug(
                f"matched decomposition rule: {self}\n\tphrase is now: "
                + " | ".join([f"{d}" for d in decomposed])
            )
            return decomposed
        return None

    def __str__(self):
        return " ".join(f"{pt}" for pt in self._parts)

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
                match_part = remaining_parts.pop(0)
                if isinstance(match_part, int):
                    decomposed.append([])
                return match_part
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

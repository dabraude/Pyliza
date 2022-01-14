import dataclasses
import logging
import typing

from .processing import ProcessingPhrase, WordMatch_t

DecompositionPattern_t = typing.List[typing.Union[int, WordMatch_t]]


class DecompositionRule:
    _log = logging.getLogger("decompose")

    def __init__(self, decompostion_parts: DecompositionPattern_t):
        if not decompostion_parts:
            raise ValueError("decomposition needs at least one part")
        self._parts = decompostion_parts
        self._min_len = sum([p if isinstance(p, int) else 1 for p in self._parts])

    @property
    def pattern(self):
        return self._parts

    def decompose(
        self, phrase: ProcessingPhrase
    ) -> typing.Union[None, typing.List[str]]:
        """Attempt to decompose the user input, return None if cannot."""
        if len(phrase) < self._min_len:
            return None

        remaining_parts = self._parts[:]
        next_keyword, int_parts = self._advance_matching(remaining_parts)
        if next_keyword is None and int_parts is None:
            self._log.error("pattern was invalid")
            return None

        unprocessed = []
        decomposed = []
        for word in phrase:
            if next_keyword is not None and word.matches(next_keyword):
                decomposed_from_int = self._decompose_int_parts(unprocessed, int_parts)
                unprocessed = []
                if decomposed_from_int is not None:
                    decomposed.extend(decomposed_from_int)
                elif int_parts:
                    return None
                decomposed.append([word])
                next_keyword, int_parts = self._advance_matching(remaining_parts)
            elif not int_parts:
                return None
            else:
                unprocessed.append(word)

        if next_keyword:
            return None

        decomposed_from_int = self._decompose_int_parts(unprocessed, int_parts)
        if decomposed_from_int is not None:
            decomposed.extend(decomposed_from_int)

        self._log.debug(
            f"matched decomposition rule: {self}\n\tphrase is now: "
            + " | ".join([f"{d}" for d in decomposed])
        )
        return decomposed

    def _advance_matching(self, remain):
        if not remain:
            return None, None
        iparts = []
        nxt = remain.pop(0)
        while remain and isinstance(nxt, int):
            iparts.append(nxt)
            nxt = remain.pop(0)
        if isinstance(nxt, int):
            return None, iparts + [nxt]
        return nxt, iparts

    def _decompose_int_parts(self, unprocessed, int_parts):
        if not int_parts:
            return None
        if len(unprocessed) < sum(int_parts):
            return None

        decomposed = []
        pre0, pst0, has0 = self._split_by_0(int_parts)
        unprocessed = self._add_elements(pre0, decomposed, unprocessed)
        unprocessed = self._add_for_0(has0, pre0, pst0, decomposed, unprocessed)
        self._add_elements(pst0, decomposed, unprocessed)
        return decomposed

    def _add_for_0(self, has0, pre0, pst0, decomposed, unprocessed):
        if not has0:
            return unprocessed

        if pst0:
            num0s = len(unprocessed) - sum(pst0)
            decomposed.append(unprocessed[:num0s])
            return unprocessed[num0s:]

        decomposed.append(unprocessed)
        return []

    def _add_elements(self, parts, decomposed, unprocessed):
        if not parts or not unprocessed:
            return unprocessed
        for v in parts:
            decomposed.append(unprocessed[:v])
            unprocessed = unprocessed[v:]
        return unprocessed

    def _split_by_0(self, int_parts):
        try:
            idx0 = int_parts.index(0)
            return (int_parts[:idx0], int_parts[idx0 + 1 :], True)
        except ValueError:
            return (int_parts, None, False)

    def __str__(self):
        return " ".join(f"{pt}" for pt in self._parts)


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

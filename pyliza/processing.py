import typing
import re

WordMatch_t = typing.Union[str, typing.Set[str]]


class ProcessingWord:
    tag_re = re.compile(r"\(/(?P<tag>\S+)\)")

    def __init__(self, word) -> None:
        self.word: str = word
        self.tags: typing.List[str] = []
        if isinstance(word, ProcessingWord):
            self.word = word.word
            self.tags = word.tags

    def __str__(self) -> str:
        return self.word + "(" + ",".join(self.tags) + ")"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return self.word.__hash__()

    def __eq__(self, other) -> bool:
        return self.word == other.word

    def __ne__(self, other) -> bool:
        return not (self == other)

    def matches(self, test: WordMatch_t) -> bool:
        if isinstance(test, str):
            return self._match(test)
        return any(map(self._match, test))

    def _match(self, test: str):
        tag_mobj = self.tag_re.match(test)
        if tag_mobj is not None:
            return self._match_tag(tag_mobj.group("tag"))
        return self.word == test

    def _match_tag(self, tag_str: str):
        return tag_str in self.tags


class ProcessingPhrase:
    def __init__(self, phrase: typing.Union[str, typing.List[ProcessingWord]]) -> None:
        self._words: typing.List[ProcessingWord] = None
        if isinstance(phrase, str):
            self._words: typing.List[ProcessingWord] = list(
                map(ProcessingWord, phrase.strip().split())
            )
        else:
            self._words = phrase[:]
        self._iter_pos = 0

    def to_string(self):
        return " ".join([f"{w.word}" for w in self._words])

    def __iter__(self):
        return self._words.__iter__()

    def __str__(self):
        return " ".join([f"{w}" for w in self._words])

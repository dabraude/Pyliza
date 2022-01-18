import typing
import re

WordMatch_t = typing.Union["ProcessingWord", typing.Set["ProcessingWord"]]


class ProcessingWord:
    tag_re = re.compile(r"\(/(?P<tag>\S+)\)")

    def __init__(self, word, tags=None) -> None:
        self.word: str = word
        self.tags: typing.Set[set] = set()
        if isinstance(word, ProcessingWord):
            self.word = word.word
            self.tags = word.tags.copy()
        elif word is not None and not isinstance(word, str):
            raise ValueError(f"word must be None or str, not {type(word)}")

        if tags is not None:
            if not isinstance(tags, set) or any(
                map(lambda s: not isinstance(s, str), tags)
            ):
                raise ValueError(f"tags must be None or a set of ProcessingWord")
            self.tags = tags.copy()

    def __neg__(self) -> bool:
        return not self.word and not self.tags

    def __str__(self) -> str:
        w = self.word if self.word is not None else "_"
        return w + "(" + ",".join(self.tags) + ")"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash((self.word, tuple(sorted(self.tags))))

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.word == other
        if isinstance(other, ProcessingWord):
            return self.word == other.word and self.tags == other.tags
        return False

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __lt__(self, other) -> bool:
        if self.word == other.word:
            return self.tags < other.tags
        return self.word < other.word

    def matches(self, test: WordMatch_t) -> bool:
        if isinstance(test, ProcessingWord):
            return self._match(test)
        return any(map(self._match, test))

    def _match(self, test: "ProcessingWord"):
        return self.word == test.word or (self.tags & test.tags)

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
        for w in self._words:
            if not isinstance(w, ProcessingWord):
                raise ValueError(
                    "A processing phrase should only have ProcessingWord in the resulting list"
                )

    def to_list(self):
        return self._words[:]

    def to_string(self):
        return " ".join([f"{w.word}" for w in self._words])

    def __iter__(self):
        return self._words.__iter__()

    def __str__(self):
        return " ".join([f"{w}" for w in self._words])

    def __repr__(self):
        return "'" + " ".join([f"{w}" for w in self._words]) + "'"

    def __len__(self):
        return len(self._words)

    def __getitem__(self, pos: int) -> ProcessingWord:
        return self._words[pos]

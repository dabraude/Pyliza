import collections
import dataclasses
import enum
import logging
import typing

from .transformation import DecompositionRule, ReassemblyRule, TransformRule
from .processing import ProcessingPhrase, ProcessingWord


class RuleType(enum.Enum):
    NONE = -1
    UNKNOWN = 0
    TRANSFORMATION = 1
    UNCONDITIONAL_SUBSTITUTION = 2
    WORD_TAGGING = 3
    EQUIVALENCE = 4
    MEMORY = 6
    # rule type 5: pre transform equivalence is actually just a vanilla transform
    # with a special reassambly rule


class ElizaRule:
    _log = logging.getLogger("ElizaRule")

    def __init__(self, substitution: typing.Optional[str], precedence: int) -> None:
        if substitution is not None and not isinstance(substitution, str):
            raise ValueError(
                f"substitution must be a string or None not {type(substitution)}"
            )
        self._substitution: typing.Optional[str] = substitution
        self._precedence: int = int(precedence)

    @property
    def precedence(self) -> int:
        return self._precedence

    def apply_substitution(self, word: ProcessingWord) -> bool:
        if not self._substitution:
            return False
        self._log.debug(f"substituting {word.word} with {self._substitution}")
        word.word = self._substitution
        return True

    def apply_transform(
        self, word: ProcessingWord, phrase: ProcessingPhrase
    ) -> typing.Tuple[typing.Optional[str], ProcessingPhrase]:
        return None, phrase


class Transformation(ElizaRule):
    def __init__(
        self,
        substitution: typing.Optional[str],
        precedence: int,
        transformation_rules: typing.Iterable[TransformRule],
    ) -> None:
        super().__init__(substitution, precedence)
        self._transformation_rules = transformation_rules

    def apply_transform(self, word, phrase):
        self._log.info(f"applying transform triggered by keyword: {word}")
        self._log.debug(f"finding decomposition for {phrase}")
        for trule in self._transformation_rules:
            lrule, new_phrase = trule.apply(phrase)
            if new_phrase is not None:
                return lrule, new_phrase
        self._log.debug("no decomposition rules matched, word may have been removed")
        return None, phrase


class UnconditionalSubstitution(ElizaRule):
    def __init__(self, substitution: str, precedence: int) -> None:
        super().__init__(substitution, precedence)
        if self._substitution is None:
            raise ValueError(
                "substitution must be set for Unconditional Substitution Rule"
            )


class TagWord(ElizaRule):
    def __init__(
        self,
        substitution: typing.Optional[str],
        precedence: int,
        dlist: typing.Iterable[str],
    ) -> None:
        super().__init__(substitution, precedence)
        self._dlist = dlist

    def tag_word(self, word: ProcessingWord):
        word.tags = self._dlist[:]
        self._log.info(f"tagged word is now {word}")


class Equivalence(ElizaRule):
    def __init__(
        self, substitution: None, precedence: int, equivalent_keyword: str
    ) -> None:
        super().__init__(substitution, precedence)
        if not isinstance(equivalent_keyword, str):
            raise ValueError(
                f"equivalent_keyword must be str for Equivalence Rule not {type(equivalent_keyword)}"
            )
        self.equivalent_keyword = ProcessingWord(equivalent_keyword)

    def apply_transform(self, word, phrase):

        return self.equivalent_keyword, phrase


class Memory(ElizaRule):
    def __init__(
        self,
        substitution: None,
        precedence: int,
        memory_rules: typing.Iterable[TransformRule],
    ) -> None:
        super().__init__(substitution, precedence)
        self._rules = memory_rules
        self._memories = []
        for mem_rule in self._rules:
            if not isinstance(mem_rule, TransformRule):
                raise ValueError("memories must be a list of TransformRules")

    def memorise(self, phrase: ProcessingPhrase) -> bool:
        for mem_rule in self._rules:
            _, new_phrase = mem_rule.apply(phrase)
            if new_phrase is not None:
                self._log.debug("memorised phrased.")
                self._memories.append(new_phrase)
                return True
        return False

    def recall(self) -> str:
        try:
            return self._memories.pop(0)
        except IndexError:
            return ""


@dataclasses.dataclass
class KeyStackedWord:
    word: ProcessingWord
    rule: ElizaRule
    org_word: ProcessingWord = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.org_word = ProcessingWord(self.word)


KeyStack_t = typing.List[KeyStackedWord]


class RuleSet:
    _log = logging.getLogger("RuleSet")

    def __init__(
        self,
        greetings: typing.List[str],
        rules: typing.Mapping[str, ElizaRule],
        memory_rules: typing.List[typing.Tuple[str, Memory]],
    ):
        self.greetings = greetings
        self.rules = {ProcessingWord(w): r for w, r in rules.items()}
        self.memory_rules = collections.OrderedDict(
            [(ProcessingWord(w), r) for w, r in memory_rules]
        )
        self._none_rule: Transformation = self.rules[ProcessingWord("NONE")]

    def get_response_for(self, phrase) -> typing.Optional[str]:
        """Build a response for a phrase or return None if not possible."""
        processing_phrase = ProcessingPhrase(phrase)
        substitution_count, keystack, memory_keystack = self._build_keystacks(
            processing_phrase
        )
        self._memorise(memory_keystack, processing_phrase)
        if not substitution_count and not keystack:
            self._log.debug(f'no keywords in "{phrase}"')
            return None
        self._log.info(
            f'found {len(keystack)} unprocessed keyword(s) and made {substitution_count} substitution(s) in "{phrase}"'
        )
        self._log.debug(
            f'after substitutions phrase is "{processing_phrase.to_string()}"'
        )

        processing_phrase = self._apply_keystack(processing_phrase, keystack)

        self._log.debug(f"finished building response")
        return processing_phrase.to_string()

    def _memorise(self, memory_keystack: KeyStack_t, phrase: ProcessingPhrase):
        """Add to memorised rules."""
        self._log.info(f"{len(memory_keystack)} memory rules have been activated.")
        for mem in memory_keystack:
            self._log.debug(f"attempting to add memory for {mem.org_word}")
            if not mem.rule.memorise(phrase):
                self._log.debug("no available decompisition rules.")

    def get_no_keyword_reponse(self) -> str:
        """Figure out a response if there were no keywords in the user input."""
        response = self._get_memory_response()
        if not response:
            response = self._get_none_response()
        return response

    def _get_memory_response(self) -> str:
        for mem_rule in self.memory_rules.values():
            response = mem_rule.recall()
            if response:
                return response.to_string()
        return ""

    def _get_none_response(self) -> str:
        _, phrase = self._none_rule.apply_transform(None, ProcessingPhrase(""))
        return phrase.to_string()

    def _build_keystacks(
        self, phrase: ProcessingPhrase
    ) -> typing.Tuple[int, KeyStack_t, KeyStack_t]:
        """Determine the keystack in the precedence order and tags the words."""
        keystack = []
        memory_keystack = []
        substitution_count = 0
        top_precedence = 0  # sorting is not straightforward
        for word in phrase:
            if word in self.memory_rules:
                memory_keystack.append(KeyStackedWord(word, self.memory_rules[word]))
            if word not in self.rules:
                continue
            rule = self.rules[word]
            if rule.apply_substitution(word):
                substitution_count += 1
            if isinstance(rule, UnconditionalSubstitution):
                continue
            if isinstance(rule, TagWord):
                rule.tag_word(word)
                continue
            if rule.precedence > top_precedence:
                keystack.insert(0, KeyStackedWord(word, rule))
                top_precedence = rule.precedence
            else:
                keystack.append(KeyStackedWord(word, rule))
        return substitution_count, keystack, memory_keystack

    def _apply_keystack(self, phrase: ProcessingPhrase, keystack: KeyStack_t):
        while keystack:
            top = keystack.pop(0)
            linked_rule_key, phrase = top.rule.apply_transform(top.word, phrase)

            if linked_rule_key is not None:
                linked_rule = self.rules.get(linked_rule_key)
                if linked_rule is not None:
                    self._log.info(
                        f"replacing rule for {top.word} with rule for {linked_rule_key}"
                    )
                    top.rule = linked_rule
                    keystack.insert(0, top)
                else:
                    self._log.error(
                        f"could not find linked rule with key: {linked_rule_key}"
                    )
        return phrase

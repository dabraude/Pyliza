import dataclasses
import enum
import logging
import random
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
    # rule type 5: pre transform equivalence is actually just a vanilla transform
    # with a special reassambly rule
    MEMORY = 6


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
        return None, None


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
        linked_rule = None
        self._log.debug(f"applying transform triggered by keyword: {word}")
        for trule in self._transformation_rules:
            decomposed = trule.decompose.match(phrase)
            if decomposed is not None:
                reassembly = random.choice(trule.reassemble)
                self._log.debug(f"applying reassembly rule: {reassembly}")
                linked_rule, phrase = reassembly.apply(decomposed)
                break

        return linked_rule, phrase


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
        self._log.debug(f"tagged word is now {word}")


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
        self._log.debug(
            f"replacing rule for {word} with rule for {self.equivalent_keyword}"
        )
        return self.equivalent_keyword, phrase


class Memory(ElizaRule):
    def __init__(
        self,
        substitution: None,
        precedence: int,
        memories: typing.Iterable[typing.Tuple[DecompositionRule, ReassemblyRule]],
    ) -> None:
        super().__init__(substitution, precedence)
        self._memories = memories
        for (dec, rss) in self._memories:
            if not isinstance(dec, DecompositionRule) or not isinstance(
                rss, ReassemblyRule
            ):
                raise ValueError(
                    "memories must be a list of tuples, (DecompositionRule, ReassemblyRule)"
                )


@dataclasses.dataclass
class KeyStackedWord:
    word: ProcessingWord
    rule: ElizaRule


KeyStack_t = typing.List[KeyStackedWord]


class RuleSet:
    _log = logging.getLogger("RuleSet")

    def __init__(
        self, greetings: typing.List[str], rules: typing.Mapping[str, ElizaRule]
    ):
        self.greetings = greetings
        self.rules = {ProcessingWord(w): r for w, r in rules.items()}

    def get_response_for(self, phrase) -> typing.Optional[str]:
        """Build a response for a phrase or return None if not possible."""
        processing_phrase = ProcessingPhrase(phrase)
        substitution_count, keystack = self._build_keystack(processing_phrase)
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

    def get_no_keyword_reponse(self):
        """Figure out a response if there were no keywords in the user input."""
        # Memory
        # None
        return "---"

    def _build_keystack(
        self, phrase: ProcessingPhrase
    ) -> typing.Tuple[int, KeyStack_t]:
        """Determine the keystack in the precedence order and tags the words."""
        keystack = []
        substitution_count = 0
        top_precedence = 0  # sorting is not straightforward
        for idx, word in enumerate(phrase):
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
        return substitution_count, keystack

    def _apply_keystack(self, phrase: ProcessingPhrase, keystack: KeyStack_t):
        while keystack:
            top = keystack.pop(0)
            linked_rule_key, phrase = top.rule.apply_transform(top.word, phrase)

            if linked_rule_key is not None:
                linked_rule = self.rules.get(linked_rule_key)
                if linked_rule is not None:
                    top.rule = linked_rule
                    keystack.insert(0, top)
                else:
                    self._log.error(
                        f"could not find linked rule with key: {linked_rule_key}"
                    )
        return phrase

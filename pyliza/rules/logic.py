import enum
import typing
import re


class RuleType(enum.Enum):
    NONE = -1
    UNKNOWN = 0
    TRANSFORMATION = 1
    UNCONDITIONAL_SUBSTITUTION = 2
    DLIST = 3
    EQUIVALENCE = 4
    # rule type 5: pre transform equivalence is actually just a vanilla transform
    # with a special reassambly rule
    MEMORY = 6


class ElizaRule:
    def __init__(self, substitution: typing.Optional[str], precedence: int) -> None:
        self._substitution: str = substitution
        self._precedence: int = int(precedence)

    @property
    def precedence(self) -> int:
        return self._precedence

    @property
    def substitution(self) -> int:
        return self._substitution


class DecompositionRule:
    def __init__(
        self, decompostion_parts: typing.List[typing.Union[int, str, typing.Set[str]]]
    ):
        self._matches: typing.List[re.Pattern] = self._convert_to_regexs(
            decompostion_parts
        )

    def match(self, user_input: str) -> typing.Union[None, typing.List[str]]:
        """Attempt to decompose the user input."""
        mobj = self._regex.match(user_input)
        if mobj is None:
            return None
        return list(mobj.groups())

    def _convert_to_regexs(self, parts):
        """Convert the decomposed parts to a regular expression."""
        pattern = "(^)"
        for idx, part in enumerate(parts):
            if isinstance(part, set):
                pattern += "(" + "|".join(part) + ")"
            elif isinstance(part, int):
                if part == 0:
                    pattern += "(.*)" if idx == len(parts) - 1 else "(.*?)"
                else:
                    pattern += "(" + "\S+\s+" * (part - 1) + "\S+\s*)"
            elif isinstance(part, str):
                pattern += f"({part})"
            else:
                raise ValueError("unexpected type in decompostion")
        pattern += "$"
        return re.compile(pattern, flags=re.DOTALL)


class Reassembly:
    def __init__(self):
        pass


class Transformation(ElizaRule):
    def __init__(
        self,
        substitution: typing.Optional[str],
        precedence: int,
        transformation_rules: typing.Iterable[
            typing.Tuple[DecompositionRule, typing.Iterable[Reassembly]]
        ],
    ) -> None:
        super().__init__(substitution, precedence)
        self._transformation_rules = transformation_rules


class UnconditionalSubstitution(ElizaRule):
    def __init__(self, substitution: str, precedence: int) -> None:
        super().__init__(substitution, precedence)
        if not isinstance(self.substitution, str):
            raise ValueError(
                "substitution must be a string for Unconditional Substitution Rule"
            )


class DList(ElizaRule):
    def __init__(
        self,
        substitution: typing.Optional[str],
        precedence: int,
        dlist: typing.Iterable[str],
    ) -> None:
        super().__init__(substitution, precedence)
        self._dlist = dlist


class Equivalence(ElizaRule):
    def __init__(
        self, substitution: None, precedence: int, equivalent_keyword: str
    ) -> None:
        super().__init__(substitution, precedence)
        self._equivalent_keyword = equivalent_keyword
        if not isinstance(self._equivalent_keyword, str):
            raise ValueError("equivalent_keyword must be a string for Equivalence Rule")


class Memory(ElizaRule):
    def __init__(
        self,
        substitution: None,
        precedence: int,
        memories: typing.Iterable[typing.Tuple[DecompositionRule, Reassembly]],
    ) -> None:
        super().__init__(substitution, precedence)
        self._memories = memories
        for (dec, rss) in self._memories:
            if not isinstance(dec, DecompositionRule) or not isinstance(
                rss, Reassembly
            ):
                raise ValueError(
                    "memories must be a list of tuples, (Decomposition, Reassembly)"
                )


class RuleSet:
    def __init__(
        self, greetings: typing.List[str], rules: typing.Mapping[str, ElizaRule]
    ):
        self.greetings = greetings
        self.rules = rules

    def check_for_keyword(self, phrase):
        phrase = phrase.strip().split()
        for word in phrase:
            if word in self.rules:
                return True
        return False

import enum
import typing


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
    def substitution(self) -> int:
        return self._precedence

    @property
    def substitution(self) -> int:
        return self._substitution


class Decomposition:
    def __init__(self):
        pass


class Reassembly:
    def __init__(self):
        pass


class Transformation(ElizaRule):
    def __init__(
        self,
        substitution: typing.Optional[str],
        precedence: int,
        transformation_rules: typing.Iterable[
            typing.Tuple[Decomposition, typing.Iterable[Reassembly]]
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
        memories: typing.Iterable[typing.Tuple[Decomposition, Reassembly]],
    ) -> None:
        super().__init__(substitution, precedence)
        self._memories = memories
        for (dec, rss) in self._memories:
            if not isinstance(dec, Decomposition) or not isinstance(rss, Reassembly):
                raise ValueError(
                    "memories must be a list of tuples, (Decomposition, Reassembly)"
                )


class RuleSet:
    def __init__(self, greetings, rules):
        self.greetings = greetings
        self.rules = rules

import enum
import logging
import re
import typing


class RuleType(enum.Enum):
    NONE = -1
    UNKNOWN = 0
    TRANSFORMATION = 1
    UNCONDITIONAL_SUBSTITUTION = 2
    DLIST = 3
    EQUIVALENCE = 4
    PRE_TRANSFORM_EQUIVALENCE = 5
    MEMORY = 6


class ElizaRule:
    def __init__(self, precidence=0) -> None:
        self._precedence: int = int(precidence)

    @property
    def precedence(self) -> int:
        return self._precedence


def parse_rule_text(rule_text: str) -> typing.Tuple[str, ElizaRule]:
    return RuleParser.parse_rule_text(rule_text)


class RuleParser:
    keyword_fixed_rule_types = {"NONE": RuleType.NONE, "MEMORY": RuleType.MEMORY}
    regex_sub_precedence = re.compile(r"\s*(=\s*(?P<sub>\S+))?\s*(?P<prec>\d+)?\s*")
    regex_dlist_check = re.compile(r"DLIST\(\s*/")
    regex_equivalence = re.compile(r"\(\s*=\s*(?P<eqv>\S+?)\s*\)$")
    regex_pre_tranform_equivalence = re.compile(
        r"\(\s*PRE\s+\(.*?\)\s*\(\s*=\s*(?P<eqv>\S+)\)\s*\)\s*\)$", flags=re.DOTALL
    )

    @classmethod
    def parse_rule_text(cls, rule_text: str) -> typing.Tuple[str, ElizaRule]:
        log = logging.getLogger("rules")

        rule_text = rule_text[1:-1].strip()  # strip the brackets
        if not rule_text:
            return None, None

        keyword, instructions = rule_text.split(maxsplit=1)
        rule_type = cls._check_for_fixed_rule_type(keyword)
        if rule_type == RuleType.NONE:
            log.debug("found 'NONE' rule")
        elif rule_type == RuleType.MEMORY:
            log.debug("found 'MEMORY' rule")
            keyword, instructions = instructions.split(maxsplit=1)

        substitution, precedence, instructions = cls._get_substitution_and_precedence(
            instructions
        )
        if rule_type is None:
            rule_type = cls._determine_rule_type(substitution, instructions)

        log.info(f"parsed rule for keyword '{keyword}' of type {rule_type.name}")
        return keyword, ElizaRule(precedence)

    @classmethod
    def _check_for_fixed_rule_type(cls, keyword) -> typing.Optional[RuleType]:
        return cls.keyword_fixed_rule_types.get(keyword)

    @classmethod
    def _get_substitution_and_precedence(
        cls,
        instructions,
    ) -> typing.Tuple[typing.Optional[str], int, str]:
        matched = cls.regex_sub_precedence.match(instructions)
        if matched is not None:
            sub = matched.group("sub")
            substitution = sub if sub is not None else None
            prec = matched.group("prec")
            precedence = int(prec) if prec is not None else 0
            instructions = instructions[matched.span()[1] :]
        else:
            substitution = None
            precedence = 0
        return substitution, precedence, instructions.strip()

    @classmethod
    def _determine_rule_type(
        cls, substitution: typing.Optional[str], instructions: str
    ) -> RuleType:
        if not instructions and substitution is not None:
            return RuleType.UNCONDITIONAL_SUBSTITUTION
        if cls.regex_dlist_check.match(instructions):
            return RuleType.DLIST
        if cls.regex_equivalence.match(instructions):
            return RuleType.EQUIVALENCE
        if cls.regex_pre_tranform_equivalence.search(
            instructions,
        ):
            return RuleType.PRE_TRANSFORM_EQUIVALENCE
        return RuleType.TRANSFORMATION

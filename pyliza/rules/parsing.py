import logging
import re
import typing

from .. import utils
from . import logic
from .logic import RuleSet, RuleType, ElizaRule


class ScriptParser:
    keyword_fixed_rule_types = {"NONE": RuleType.NONE, "MEMORY": RuleType.MEMORY}
    regex_sub_precedence = re.compile(r"\s*(=\s*(?P<sub>\S+))?\s*(?P<prec>\d+)?\s*")
    regex_dlist_check = re.compile(r"DLIST\(\s*/")
    regex_equivalence = re.compile(r"\(\s*=\s*(?P<eqv>\S+?)\s*\)$")
    regex_pre_transform_equivalence = re.compile(
        r"\(\s*PRE\s+\(.*?\)\s*\(\s*=\s*(?P<eqv>\S+)\)\s*\)\s*\)$", flags=re.DOTALL
    )

    @classmethod
    def parse_rule_file(cls, script):
        log = logging.getLogger("script")
        log.info("parsing script file")
        raw_script = cls._strip_script(script)
        rules_started = False
        greetings = []
        rules = {}
        for rule_text in cls._rule_texts(raw_script):
            if rule_text == "START":
                rules_started = True
                continue
            # Until the rule set is started the script is just a list of possible
            # greetings.
            if not rules_started:
                rule_text = rule_text[1:-1]
                greetings.append(rule_text + "\n")
                continue
            keyword, rule = cls.parse_rule_text(rule_text)
            rules[keyword] = rule

        log.info(f"loaded {len(greetings)} greetings and {len(rules)} rules.")

        if not rules_started:
            raise ValueError(
                "missing 'START' keyword to indicate the start of the rule set and end of greetings."
            )

        return RuleSet(greetings, rules)

    @classmethod
    def _strip_script(cls, script: typing.Iterable[str]) -> str:
        """Remove comments and surrounding whitespace, stops processing after ()."""
        script_text = "\n".join(
            [
                line
                for line in map(str.strip, script)
                if line and not line.startswith(";")
            ]
        )
        end_of_script = re.search("\(\s*\).*$", script_text, flags=re.DOTALL)
        script_text = script_text[: end_of_script.start()]
        return script_text.strip()

    @classmethod
    def _rule_texts(cls, raw_script: str) -> str:
        """Generator that iterates through rules."""
        while raw_script:
            raw_rule, end_pos = cls._next_raw_rule(raw_script)
            yield raw_rule
            raw_script = raw_script[end_pos:]

    @classmethod
    def _next_raw_rule(self, raw_script: str) -> typing.Tuple[str, int]:
        """Find the next rule in the script text."""
        start_match = re.match(r"\s*?START\s", raw_script)
        if start_match is not None:
            return "START", start_match.end()
        return utils.get_bracketed_text(raw_script)

    @classmethod
    def parse_rule_text(cls, rule_text: str) -> typing.Tuple[str, ElizaRule]:
        """Convert text to a keyword and rule."""
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
        if rule_type == RuleType.UNKNOWN:
            rule_type = cls._determine_rule_type(substitution, instructions)

        rule = cls._parse_rule_instructions(
            substitution, precedence, rule_type, instructions
        )
        log.info(f"parsed rule for keyword '{keyword}' of type {rule_type.name}")
        return keyword, rule

    @classmethod
    def _check_for_fixed_rule_type(cls, keyword) -> RuleType:
        """Check if the keyword is reserved."""
        return cls.keyword_fixed_rule_types.get(keyword, RuleType.UNKNOWN)

    @classmethod
    def _get_substitution_and_precedence(
        cls,
        instructions,
    ) -> typing.Tuple[typing.Optional[str], int, str]:
        """Get the substitution and the precidence if available."""
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
        """Based on the instructions figure out what type of rule we have."""
        if not instructions and substitution is not None:
            return RuleType.UNCONDITIONAL_SUBSTITUTION
        if cls.regex_dlist_check.match(instructions):
            return RuleType.DLIST
        if cls.regex_equivalence.match(instructions):
            return RuleType.EQUIVALENCE
        if cls.regex_pre_transform_equivalence.search(
            instructions,
        ):
            return RuleType.PRE_TRANSFORM_EQUIVALENCE
        return RuleType.TRANSFORMATION

    @classmethod
    def _parse_rule_instructions(
        cls,
        substitution: typing.Optional[str],
        precedence: int,
        rule_type: RuleType,
        instructions: str,
    ) -> ElizaRule:
        instruction_parsers = {
            RuleType.NONE: _RuleInstructionParser,
            RuleType.TRANSFORMATION: _RuleInstructionParser,
            RuleType.UNCONDITIONAL_SUBSTITUTION: UnconditionalSubstitutionParser,
            RuleType.DLIST: _RuleInstructionParser,
            RuleType.EQUIVALENCE: EquivalenceParser,
            RuleType.PRE_TRANSFORM_EQUIVALENCE: _RuleInstructionParser,
            RuleType.MEMORY: _RuleInstructionParser,
        }
        rule = instruction_parsers[rule_type].parse_instruction_text(
            substitution, precedence, instructions
        )
        return rule


class _RuleInstructionParser:
    @classmethod
    def parse_instruction_text(
        cls, substitution, precedence, instructions
    ) -> ElizaRule:
        return ElizaRule(substitution, precedence)
        raise NotImplementedError("need to implement parse_instruction_text")


class EquivalenceParser(_RuleInstructionParser):
    regex_equivalence = ScriptParser.regex_equivalence

    @classmethod
    def parse_instruction_text(
        cls, substitution, precedence, instructions
    ) -> ElizaRule:
        mobj = cls.regex_equivalence.match(instructions)
        equivalent_keyword = mobj.group("eqv")
        return logic.Equivalence(substitution, precedence, equivalent_keyword)


class UnconditionalSubstitutionParser(_RuleInstructionParser):
    @classmethod
    def parse_instruction_text(cls, substitution, precedence, _) -> ElizaRule:
        return logic.UnconditionalSubstitution(substitution, precedence)

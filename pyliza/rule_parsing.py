import logging
import re
import typing
from typing import Optional, Tuple

from . import utils
from . import ruleset
from .ruleset import RuleSet, RuleType, ElizaRule
from .transformation import TransformRule, DecompositionRule, ReassemblyRule


class ScriptParser:
    @classmethod
    def parse(cls, script):
        log = logging.getLogger("script")
        log.info("parsing script file")
        raw_script = cls._strip_script(script)
        try:
            greetings_text, rules_text = raw_script.split("START")
        except ValueError:
            raise ValueError(
                "missing 'START' keyword to indicate the start of the rule set and end of greetings."
            )
        greetings = cls._parse_greetings(greetings_text)
        rules = cls._parse_rules(rules_text)
        log.info(f"loaded {len(greetings)} greetings and {len(rules)} rules.")
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
    def _parse_greetings(cls, greetings_text: str) -> typing.List[str]:
        """Retrieves all the greetings."""
        greetings_text = greetings_text.strip()
        greetings = [greet + "\n" for greet in utils.bracket_iter(greetings_text)]
        return greetings

    @classmethod
    def _parse_rules(cls, rules_text: str) -> typing.Mapping[str, ElizaRule]:
        """Parse the text of the rules."""
        rules = {}
        for rule_text in utils.bracket_iter(rules_text):
            keyword, rule = RuleParser.parse(rule_text)
            rules[keyword] = rule
        return rules


class RuleParser:
    log = logging.getLogger("rules")

    keyword_fixed_rule_types = {"NONE": RuleType.NONE, "MEMORY": RuleType.MEMORY}
    consuming_keyword = {"MEMORY"}

    sub_split_re = re.compile(r"(\S+)(.*)", flags=re.DOTALL)
    dlist_re = re.compile(r"DLIST\(\s*/")
    equivalence_re = re.compile(r"\(\s*=\s*(?P<eqv>\S+?)\s*\)$")

    @classmethod
    def parse(cls, rule_text) -> Tuple[str, ElizaRule]:
        """Convert rule text into keyword and logic rule."""
        keyword, rule_type, rule_text = cls._parse_keyword(rule_text)
        substitution, rule_text = cls._parse_substitution(rule_text)
        precedence, rule_text = cls._parse_precedence(rule_text)
        rule, rule_type = cls._parse_instructions(
            rule_type, substitution, precedence, rule_text
        )
        cls.log.info(f"parsed rule for keyword '{keyword}' of type {rule_type.name}")
        return keyword, rule

    @classmethod
    def _parse_keyword(cls, rule_text) -> Tuple[str, RuleType, str]:
        """Gets the keyword and rule type if it was set by the keyword."""
        keyword, rule_text = rule_text.split(maxsplit=1)
        rule_type = cls.keyword_fixed_rule_types.get(keyword, RuleType.UNKNOWN)
        if keyword in cls.consuming_keyword:
            keyword, rule_text = rule_text.split(maxsplit=1)
        cls.log.debug(
            f"found keyword '{keyword}' with keyword set rule type {rule_type.name}"
        )
        return keyword, rule_type, rule_text.strip()

    @classmethod
    def _parse_substitution(cls, rule_text: str) -> Tuple[Optional[str], str]:
        """Pulls out the direct substitution."""
        if not rule_text.startswith("="):
            return None, rule_text

        rule_text = rule_text[1:].lstrip()
        if rule_text.startswith("("):
            substitution, endpos = utils.get_bracketed_text(rule_text, False)
            rule_text = rule_text[endpos:]
        else:
            substitution, rule_text = cls.sub_split_re.match(rule_text).groups()
        cls.log.debug(f"found substitution '{substitution}'")
        return substitution, rule_text.strip()

    @classmethod
    def _parse_precedence(cls, rule_text: str) -> Tuple[int, str]:
        """Pulls out the precedence."""
        precedence_mobj = re.match(r"(\d*)(.*)", rule_text, re.DOTALL)
        precedence_str, rule_text = precedence_mobj.groups()
        precedence = int(precedence_str) if precedence_str else 0
        cls.log.debug(f"setting precedence to {precedence}")
        return precedence, rule_text.strip()

    @classmethod
    def _parse_instructions(cls, rule_type, substitution, precedence, rule_text):
        rule_type = cls._determine_rule_type(rule_type, substitution, rule_text)
        cls.log.info(f"rule type set to {rule_type.name}")
        instruction_parsers = {
            RuleType.NONE: TransformationParser,
            RuleType.TRANSFORMATION: TransformationParser,
            RuleType.UNCONDITIONAL_SUBSTITUTION: UnconditionalSubstitutionParser,
            RuleType.DLIST: DListParser,
            RuleType.EQUIVALENCE: EquivalenceParser,
            RuleType.MEMORY: MemoryParser,
        }
        rule = instruction_parsers[rule_type].parse(substitution, precedence, rule_text)
        return rule, rule_type

    @classmethod
    def _determine_rule_type(
        cls, rule_type: RuleType, substitution: Optional[str], instructions: str
    ) -> RuleType:
        """Based on the instructions figure out what type of rule we have."""
        if rule_type != RuleType.UNKNOWN:
            return rule_type
        if not instructions and substitution is not None:
            return RuleType.UNCONDITIONAL_SUBSTITUTION
        if cls.dlist_re.match(instructions):
            return RuleType.DLIST
        if cls.equivalence_re.match(instructions):
            return RuleType.EQUIVALENCE
        return RuleType.TRANSFORMATION


class DecompositionParser:
    @classmethod
    def parse(cls, text) -> DecompositionRule:
        return DecompositionRule(list(cls._parts(text)))

    @classmethod
    def _parts(cls, text):
        text = text.strip()
        while text:
            part, text = cls._options_part(text)
            if part is None:
                part, text = cls._next_part(text)
            yield part

    @classmethod
    def _options_part(cls, text):
        part = None
        if text.startswith("(*"):
            part, endpos = utils.get_bracketed_text(text)
            part = set(part[1:].strip().split())
            text = text[endpos:]
        return part, text

    @classmethod
    def _next_part(cls, text):
        mobj = re.match(r"\S+", text)
        try:
            part = int(mobj.group())
        except ValueError:
            part = mobj.group()
        text = text[mobj.end() :].lstrip()
        return part, text


class ReassemblyParser:
    @classmethod
    def parse(cls, text) -> ReassemblyRule:
        return ruleset.ReassemblyRule()


class _RuleInstructionParser:
    log = logging.getLogger("instructions")

    @classmethod
    def parse(cls, substitution, precedence, instructions) -> ElizaRule:
        raise NotImplementedError("need to implement 'parse'")


class TransformationParser(_RuleInstructionParser):
    @classmethod
    def parse(cls, substitution, precedence, instructions) -> ElizaRule:
        transformation_rules = []
        for transformation in utils.bracket_iter(instructions):
            decomp, *reassem = utils.split_brackets(transformation)
            transformation_rules.append(
                TransformRule(
                    DecompositionParser.parse(decomp),
                    list(map(ReassemblyParser.parse, reassem)),
                )
            )
        cls.log.debug(f"found {len(transformation_rules)} transformation rules")
        return ruleset.Transformation(substitution, precedence, transformation_rules)


class UnconditionalSubstitutionParser(_RuleInstructionParser):
    @classmethod
    def parse(cls, substitution, precedence, _) -> ElizaRule:
        return ruleset.UnconditionalSubstitution(substitution, precedence)


class DListParser(_RuleInstructionParser):
    dlist_re = re.compile(r"\s*DLIST\(/")

    @classmethod
    def parse(cls, substitution, precedence, instructions) -> ElizaRule:
        instructions = cls.dlist_re.sub("", instructions)[:-1].strip()
        dlist = instructions.split()
        return ruleset.TagWord(substitution, precedence, dlist)


class EquivalenceParser(_RuleInstructionParser):
    equivalence_re = re.compile(r"\(\s*=\s*(?P<eqv>\S+?)\s*\)$")

    @classmethod
    def parse(cls, substitution, precedence, instructions) -> ElizaRule:
        mobj = cls.equivalence_re.match(instructions)
        equivalent_keyword = mobj.group("eqv")
        return ruleset.Equivalence(substitution, precedence, equivalent_keyword)


class MemoryParser(_RuleInstructionParser):
    @classmethod
    def parse(cls, substitution, precedence, instructions) -> ElizaRule:
        memories = []
        for memory_pattern in utils.bracket_iter(instructions):
            decomposition_text, reassembly_text = memory_pattern.split("=")
            decomposition = DecompositionParser.parse(decomposition_text)
            reassembly = ReassemblyParser.parse(reassembly_text)
            memories.append((decomposition, reassembly))
        return ruleset.Memory(substitution, precedence, memories)

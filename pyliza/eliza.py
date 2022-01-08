import logging
import typing
import random
import re

from . import rules, utils


class Eliza:
    def __init__(self, script: typing.Iterable[str]):
        self._greatings: typing.List[str] = []
        self._rules: typing.Mapping[str, rules.ElizaRule] = {}
        self._parse_script_file(script)

    def greet(self) -> str:
        """Pick a random greeting from the available options."""
        return random.choice(self._greatings)

    def respond_to(self, user_input: str) -> str:
        user_input = user_input.upper()
        return user_input.strip() + "\n"

    def _parse_script_file(self, script: typing.Iterable[str]) -> None:
        """Convert a script file into a rule set."""
        log = logging.getLogger("script")
        log.info("parsing script file")
        raw_script = self._strip_script(script)
        rules_started = False
        for rule_text in self._rule_texts(raw_script):
            if rule_text == "START":
                rules_started = True
                continue
            # Until the rule set is started the script is just a list of possible
            # greetings.
            if not rules_started:
                rule_text = rule_text[1:-1]
                self._greatings.append(rule_text + "\n")
                continue
            keyword, rule = rules.parse_rule_text(rule_text)
            self._rules[keyword] = rule

        log.info(
            f"loaded {len(self._greatings)} greetings and {len(self._rules)} rules."
        )

        if not rules_started:
            raise ValueError(
                "missing 'START' keyword to indicate the start of the rule set and end of greetings."
            )

    def _strip_script(self, script: typing.Iterable[str]) -> str:
        """Remove comments and surrounding whitespace."""
        return "\n".join(
            [
                line
                for line in map(str.strip, script)
                if line and not line.startswith(";")
            ]
        )

    def _rule_texts(self, raw_script: str) -> str:
        """Generator that iterates through rules."""
        while raw_script:
            raw_rule, end_pos = self._next_raw_rule(raw_script)
            yield raw_rule
            raw_script = raw_script[end_pos:]

    def _next_raw_rule(self, raw_script: str) -> typing.Tuple[str, int]:
        """Find the next rule in the script text."""
        start_match = re.match(r"\s*?START\s", raw_script)
        if start_match is not None:
            return "START", start_match.span()[1]
        return utils.get_bracketed_text(raw_script)
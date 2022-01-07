import logging
import typing
import random
import re


class ElizaScript:
    def __init__(self, script: typing.Iterable[str]):
        self._greatings = []
        self._parse_script_file(script)

    def greet(self):
        return random.choice(self._greatings)

    def _parse_script_file(self, script: typing.Iterable[str]):
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
                self._greatings.append(rule_text)
                continue

        if not rules_started:
            raise ValueError(
                "missing 'START' keyword to indicate the start of the rule set and end of greetings."
            )

    def _strip_script(self, script: typing.Iterable[str]):
        """Remove comments and surrounding whitespace."""
        return "\n".join(
            [
                line
                for line in map(str.strip, script)
                if line and not line.startswith(";")
            ]
        )

    def _rule_texts(self, raw_script: str):
        """Generator that iterates through rules."""
        while raw_script:
            raw_rule, end_pos = self._next_raw_rule(raw_script)
            yield raw_rule
            raw_script = raw_script[end_pos:]

    def _next_raw_rule(self, raw_script: str):
        """Find the next rule in the script text."""
        start_match = re.match(r"\s*?START\s", raw_script)
        if start_match is not None:
            return "START", start_match.span()[1]

        num_open_brackets = 1
        num_close_brackets = False
        while num_open_brackets != num_close_brackets:
            pattern = r"\s*\((.*?\))" + f"{{{num_open_brackets}}}"
            open_to_close = re.match(pattern, raw_script, re.DOTALL)
            if open_to_close is None:
                raise ValueError(
                    "mismatching amount of brackets, or string does not start with an open bracket."
                )
            end_pos = open_to_close.span()[1]
            matched_area = raw_script[:end_pos]
            num_open_brackets = matched_area.count("(")
            num_close_brackets = matched_area.count(")")
        return matched_area.strip(), end_pos

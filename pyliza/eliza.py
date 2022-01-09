import logging
import typing
import random
import re

from . import rules
from . import utils


class Eliza:
    def __init__(self, script: typing.Iterable[str]):
        self._rule_set = None
        self._parse_script_file(script)

    def greet(self) -> str:
        """Pick a random greeting from the available options."""
        return random.choice(self._rule_set.greetings)

    def respond_to(self, user_input: str) -> str:
        user_input = user_input.upper()
        return user_input.strip() + "\n"

    def _parse_script_file(self, script: typing.Iterable[str]) -> None:
        """Convert a script file into a rule set."""
        self._rule_set = rules.RuleParser.parse_rule_file(script)

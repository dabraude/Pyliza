import logging
import typing
import random
import re

from .rule_parsing import ScriptParser
from . import utils


class Eliza:
    none_re = re.compile("(^|\s)NONE(\s|$)")
    memory_re = re.compile("(^|\s)MEMORY(\s|$)")
    rev_none_re = re.compile("(^|\s)zNONE(\s|$)")
    rev_memory_re = re.compile("(^|\s)zMEMORY(\s|$)")

    def __init__(self, script: typing.Iterable[str]):
        self._rule_set = ScriptParser.parse(script)

    def greet(self) -> str:
        """Pick a random greeting from the available options."""
        return random.choice(self._rule_set.greetings)

    def respond_to(self, user_input: str) -> str:
        """Get the appropriate response to the user."""
        u_input = self.none_re.sub("zNONE", user_input.upper())
        u_input = self.memory_re.sub("zMEMORY", u_input)

        response = None
        for phrase in utils.split_phrases(u_input):
            response = self._rule_set.get_response_for(phrase)
            if response is not None:
                break

        if response is None:
            response = self._rule_set.get_no_keyword_reponse()

        return self._finalise_response(response)

    def _finalise_response(self, response: str) -> str:
        response = self.rev_none_re.sub("NONE", response)
        response = self.rev_memory_re.sub("MEMORY", response)
        return response.strip() + "\n"

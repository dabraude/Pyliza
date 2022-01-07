import copy
import logging
import typing
import re


def parse_script_file(script: typing.Iterable[str]):
    log = logging.getLogger("script")
    log.info("parsing script file")
    raw_script = finalise_script(script)
    for rule_text in _raw_rules(raw_script):
        print()
        print(rule_text)
        print()


def _raw_rules(raw_script: str):
    """generator for finding the next rule"""
    remaining_text = copy.copy(raw_script)
    while remaining_text:
        raw_rule, end_pos = _next_raw_rule(remaining_text)
        yield raw_rule
        remaining_text = remaining_text[end_pos:]


def _next_raw_rule(raw_script: str):
    """generator for finding the next rule"""
    start_match = re.match(r"\s*?START\s", raw_script)
    if start_match is not None:
        return "START", start_match.span()[1]

    num_open_brackets = 1
    num_close_brackets = 0
    while num_open_brackets != num_close_brackets:
        pattern = r"\((.*?\))" + f"{{{num_open_brackets}}}"
        open_to_close = re.search(pattern, raw_script, re.DOTALL)
        end_pos = open_to_close.span()[1]
        matched_area = raw_script[open_to_close.span()[0] : end_pos]
        num_open_brackets = matched_area.count("(")
        num_close_brackets = matched_area.count(")")
    return matched_area, end_pos


def finalise_script(script: typing.Iterable[str]):
    """Remove comments and surrounding whitespace."""
    return "\n".join(
        [line for line in map(str.strip, script) if line and not line.startswith(";")]
    )

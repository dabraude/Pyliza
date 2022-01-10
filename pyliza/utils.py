import copy
import re
import typing


def get_bracketed_text(
    text: str, strip_brackets: bool = True
) -> typing.Tuple[str, int]:
    """Gets a text incased in brackets.

    @returns: text in the bracket, end position of the text
    """
    num_open_brackets = 1
    num_brackets_to_close = False
    while num_open_brackets != num_brackets_to_close:
        num_brackets_to_close = num_open_brackets
        pattern = r"\s*\((.*?\))" + f"{{{num_brackets_to_close}}}" + r"\s*"
        first_open_to_final_close = re.match(pattern, text, re.DOTALL)
        if first_open_to_final_close is None:
            raise ValueError(
                "mismatching amount of brackets, or string does not start with an open bracket."
            )
        end_pos = first_open_to_final_close.end()
        matched_area = text[:end_pos]
        num_open_brackets = matched_area.count("(")
    matched_area = matched_area.strip()
    if strip_brackets:
        matched_area = matched_area[1:-1].strip()
    return matched_area, end_pos


def bracket_iter(text: str, strip_brackets: bool = True) -> str:
    """Iterator for going over a list of bracketed text."""
    remaining = copy.copy(text)
    while remaining:
        bracketed_text, end_pos = get_bracketed_text(remaining, strip_brackets)
        yield bracketed_text
        remaining = remaining[end_pos:]


def split_brackets(text: str, strip_brackets: bool = True):
    """Breaks up text by brackets."""
    return [brack_text for brack_text in bracket_iter(text, strip_brackets)]


def split_phrases(text: str):
    """Goes through text phrase by phrase."""
    return list(map(str.strip, re.split(r"([?!.,-;]+)", text)))

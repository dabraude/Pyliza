import copy
import re
import typing


def get_bracketed_text(
    text: str, strip_brackets: bool = False
) -> typing.Tuple[str, int]:
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


def bracket_iter(text: str, strip_brackets: bool = False) -> str:
    remaining = copy.copy(text)
    while remaining:
        bracketed_text, end_pos = get_bracketed_text(remaining, strip_brackets)
        yield bracketed_text
        remaining = remaining[end_pos:]

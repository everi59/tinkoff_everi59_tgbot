import re
from re import Match


def check_name(name: str) -> Match[str] | None:
    return re.fullmatch(r"""[а-яА-Яa-zA-Z0-9-]{2,30}""", name)

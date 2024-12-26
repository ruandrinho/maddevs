"""
Contains function `split_message` that splits HTML-formatted message into fragments
Could be launched as `python msg_split.py --max-len 4096 source.html`
"""

from typing import Generator, Optional

import click
from bs4 import BeautifulSoup, Tag

MAX_LEN = 4096


def split_message(source: str, max_len: int = MAX_LEN) -> Generator[str]:
    """Splits the original message (`source`) into fragments of the specified length (`max_len`)."""
    while source:
        tail_start, tail_end = [], []
        fragment = __do_split(source, max_len, tail_start, tail_end)
        if not fragment:
            raise ValueError("max_len is too low")
        yield fragment
        source = "".join(tail_start + tail_end)


def __preprocess_large_strings(soup: BeautifulSoup, max_len: int) -> str:
    """Splits large text nodes into fragments"""
    for element in soup.find_all(string=True):
        if len(element) <= max_len:
            continue
        fragments = list(__split_string_into_fragments(element, max_len))
        element.replace_with(*fragments)
    return soup


def __split_string_into_fragments(text: str, max_len: int) -> Generator[str]:
    """Splits a large string into fragments of max_len without breaking words"""
    while len(text) > max_len:
        chunk = text[:max_len]
        last_space = chunk.rfind(" ")
        if last_space == -1:
            yield chunk
            text = text[max_len:]
        else:
            yield chunk[: last_space + 1]
            text = text[last_space + 1 :]
    if text:
        yield text


def __join_chunks(chunks: list) -> str:
    return "".join([str(chunk) for chunk in chunks])


def __do_split(message: str, max_len: int, tail_start: list[str], tail_end: list[str]) -> str:
    soup = BeautifulSoup(message, "html.parser")
    # TODO: find an optimal argument instead of max(max_len // 2, 20)
    soup = __preprocess_large_strings(soup, max(max_len // 2, 20))
    chunks = []
    if len(soup.contents) == 1 and isinstance(soup.contents[0], Tag):
        contents = soup.contents[0].contents
    else:
        contents = soup.contents
    wrapping_start, wrapping_end = "", ""
    for i, chunk in enumerate(contents):
        if i == 0 and not isinstance(chunk.parent, BeautifulSoup):
            wrapping_start = f"{str(chunk.parent).split('>', maxsplit=1)[0]}>"
            wrapping_end = f"</{chunk.parent.name}>"
        chunks.append(chunk)
        if len(__join_chunks(chunks) + wrapping_start + wrapping_end) > max_len:
            break
    else:
        return __join_chunks(chunks)
    valid_message = __join_chunks(chunks[:i])
    if not valid_message and not wrapping_start:
        tail_end.insert(0, __join_chunks(contents[i:]))
        return ""
    if wrapping_start:
        tail_start.append(wrapping_start)
        tail_end.insert(0, wrapping_end)
    max_len -= len(valid_message + wrapping_start + wrapping_end)
    if max_len < 0:
        tail_end.insert(0, __join_chunks(contents[i:]))
        return ""
    tail_end.insert(0, __join_chunks(contents[i + 1 :]))
    return wrapping_start + valid_message + __do_split(str(chunk), max_len, tail_start, tail_end) + wrapping_end


@click.command()
@click.option("--max-len", default=MAX_LEN, type=click.IntRange(min=1), help="Max length of splitted message")
@click.argument("filename")
def __execute(max_len: int = MAX_LEN, filename: Optional[str] = None) -> None:
    try:
        with open(filename, encoding="utf-8") as file:
            source = file.read()
        for number, message in enumerate(split_message(source, max_len), start=1):
            print(f"fragment #{number}: {len(message)} chars")
            print(message)
    except FileNotFoundError:
        print(f"No such file: '{source}'")


if __name__ == "__main__":
    __execute()

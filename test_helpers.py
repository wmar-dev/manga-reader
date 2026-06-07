import pytest
from helpers import chapter_label


@pytest.mark.parametrize("manga, chapter, expected", [
    # Standard hyphen-separated prefix
    ("bladestorm", "bladestorm-001", "Chapter 001"),
    # Decimal chapter encoded with hyphen
    ("bladestorm", "bladestorm-029-5", "Chapter 029.5"),
    # Decimal chapter encoded with dot
    ("bladestorm", "bladestorm-029.5", "Chapter 029.5"),
    # No prefix in chapter name
    ("bladestorm", "001", "Chapter 001"),
    # Manga name ends with a number — core regression: number from title must not be mistaken for chapter number
    ("iron-fist-2", "iron-fist-2-005", "Chapter 005"),
    ("void-runner-42", "void-runner-42-010", "Chapter 010"),
    # Space-separated manga name ending with a number
    ("Iron Fist 2", "Iron Fist 2 005", "Chapter 005"),
    ("Void Runner 42", "Void Runner 42 010", "Chapter 010"),
    # Manga name ending with a number, decimal chapter
    ("iron-fist-2", "iron-fist-2-029-5", "Chapter 029.5"),
    # Manga name containing a number in the middle
    ("zone-51-archives", "zone-51-archives-003", "Chapter 003"),
])
def test_chapter_label(manga, chapter, expected):
    assert chapter_label(manga, chapter) == expected

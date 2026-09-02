"""The 63-word pool and get_word behavior from python-lorem 1.3.0.post3.

Copyright (c) 2019, Jarry Shaw. Distributed under the BSD 3-Clause License.
The complete upstream license is at https://github.com/JarryShaw/lorem/blob/master/LICENSE.
"""

from __future__ import annotations

import random


WORD_POOL = (
    "ad", "adipiscing", "aliqua", "aliquip", "amet", "anim", "aute", "cillum", "commodo",
    "consectetur", "consequat", "culpa", "cupidatat", "deserunt", "do", "dolor", "dolore",
    "duis", "ea", "eiusmod", "elit", "enim", "esse", "est", "et", "eu", "ex", "excepteur",
    "exercitation", "fugiat", "id", "in", "incididunt", "ipsum", "irure", "labore", "laboris",
    "laborum", "lorem", "magna", "minim", "mollit", "nisi", "non", "nostrud", "nulla",
    "occaecat", "officia", "pariatur", "proident", "qui", "quis", "reprehenderit", "sed",
    "sint", "sit", "sunt", "tempor", "ullamco", "ut", "velit", "veniam", "voluptate",
)


def get_word(count: int) -> str:
    """Return ``count`` words using python-lorem's shuffled duplicated pool."""
    pool = list(WORD_POOL) * count
    random.shuffle(pool)
    return " ".join(pool[:count])

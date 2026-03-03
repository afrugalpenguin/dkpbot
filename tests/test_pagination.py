from pagination import paginate_list


def test_paginate_single_page():
    items = list(range(5))
    pages = paginate_list(items, per_page=10)
    assert len(pages) == 1
    assert pages[0] == [0, 1, 2, 3, 4]


def test_paginate_multiple_pages():
    items = list(range(25))
    pages = paginate_list(items, per_page=10)
    assert len(pages) == 3
    assert len(pages[0]) == 10
    assert len(pages[1]) == 10
    assert len(pages[2]) == 5


def test_paginate_empty():
    pages = paginate_list([], per_page=10)
    assert len(pages) == 1
    assert pages[0] == []


def test_paginate_exact_fit():
    items = list(range(10))
    pages = paginate_list(items, per_page=10)
    assert len(pages) == 1

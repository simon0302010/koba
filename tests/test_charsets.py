from koba.core import charsets

def test_get_range_ascii():
    chars = charsets.get_range(32, 126)
    assert len(chars) == 95
    assert ' ' in chars
    assert '~' in chars
    assert '\n' not in chars

def test_get_range_single_char():
    chars = charsets.get_range(65, 65)
    assert chars == ['A']

def test_get_range_empty():
    chars = charsets.get_range(100, 90)
    assert len(chars) == 0

def test_get_amount():
    chars = charsets.get_amount(10)
    assert len(chars) == 10
    assert all(c.isprintable() for c in chars)

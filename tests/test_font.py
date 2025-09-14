from koba.core import font

def test_get_supported_font():
    font_path = font.get_supported_font("a")
    if font_path:
        assert True
    else:
        assert False
        
def test_get_monospace_font():
    font_path = font.get_monospace_font()
    if font_path:
        assert True
    else:
        assert False
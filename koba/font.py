import matplotlib.font_manager as fm


def get_fonts():
    font_paths = []
    font_list = fm.fontManager.ttflist

    for font in font_list:
        font_paths.append(font.fname)

    return font_paths
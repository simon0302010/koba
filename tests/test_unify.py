import numpy as np
import pytest
from koba.core import unify


ENGINES = ["brightness", "ssim", "diff", "mse", "ncc", "hist", "cosine"]

# compare identical arrays
@pytest.mark.parametrize("engine", ENGINES)
def test_compare_perfect_match(engine, mocker):
    block = np.full((10, 10), 128, dtype=np.uint8)

    mocker.patch('koba.core.unify.get_char', return_value=block)

    similarity = unify.compare_character('a', block, False, engine)

    if engine == 'hist':
        # hist produces a larger error than the other engines
        assert similarity == pytest.approx(1.0, abs=1e-2)
    else:
        assert similarity == pytest.approx(1.0)

# compare black block to white block
@pytest.mark.parametrize("engine", ENGINES)
def test_compare_perfect_mismatch(engine, mocker):

    black_block = np.zeros((10, 10), dtype=np.uint8)
    white_block = np.full((10, 10), 255, dtype=np.uint8)

    mocker.patch('koba.core.unify.get_char', return_value=white_block)

    similarity = unify.compare_character('a', black_block, False, engine)

    if engine == 'ssim':
        # ssim can have a small error
        assert similarity == pytest.approx(0.0, abs=1e-4)
    else:
        assert similarity == pytest.approx(0.0)

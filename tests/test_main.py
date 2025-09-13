from click.testing import CliRunner
from koba.main import main
from PIL import Image
import os
import pytest

def test_cli_runs_successfully(monkeypatch):
    # mock get_terminal_size to avoid errors
    monkeypatch.setattr(os, 'get_terminal_size', lambda: os.terminal_size((80, 24)))

    runner = CliRunner()
    img = Image.new('L', (20, 20), color='black')
    test_image_path = 'test_image.png'
    img.save(test_image_path)

    result = runner.invoke(main, [test_image_path, '--engine', 'brightness'])

    os.remove(test_image_path)

    assert result.exit_code == 0
    assert result.output.strip() != ""

def test_cli_file_not_found():
    runner = CliRunner()
    result = runner.invoke(main, ['non_existent_file.png'])

    assert result.exit_code != 0
    assert "does not exist" in result.output

def test_cli_bad_char_range(caplog):
    runner = CliRunner()
    img = Image.new('L', (10, 10), color='black')
    test_image_path = 'test_image.png'
    img.save(test_image_path)

    result = runner.invoke(main, [test_image_path, '--char-range', 'invalid-range'])

    os.remove(test_image_path)

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Wrong format for char-range." in caplog.text
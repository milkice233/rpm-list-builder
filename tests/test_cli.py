"""Test argument parsing"""

import os
import logging
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from rpmlb import LOG
from rpmlb.cli import run


# Module-level CLI runner
runner = CliRunner()


def test_parse_argv_no_options(tmpdir):
    """Tests proper default values of the CLI"""

    RECIPE_FILE = tmpdir.join('ror.yml')
    RECIPE_NAME = 'rh-ror50'

    # Prepare environment
    RECIPE_FILE.write('')

    # Parse the arguments
    with tmpdir.as_cwd():
        argv = list(map(str, [RECIPE_FILE, RECIPE_NAME]))
        args = run.make_context('rpmlb', argv).params

    current_dir = os.path.abspath(os.getcwd())

    assert args['recipe_file'] == str(RECIPE_FILE), 'Wrong recipe file path'
    assert args['recipe_name'] == str(RECIPE_NAME), 'Wrong recipe name'
    assert args['build'] == 'dummy', 'Wrong builder name'
    assert args['download'] == 'none', 'Wrong downloader name'
    assert args['branch'] is None, 'Superfluous branch'
    assert args['source_directory'] == current_dir


@runner.isolated_filesystem()
def test_log_verbosity():
    """Ensure that the verbosity is set properly on."""

    # Initial state – if the test fails here, the app has changed
    # and the test needs to be adjusted.
    assert LOG.getEffectiveLevel() == logging.INFO

    recipe = Path('recipe.yml')
    recipe.touch()

    runner.invoke(run, ['--verbose', str(recipe), 'test'])
    assert LOG.getEffectiveLevel() == logging.DEBUG

    runner.invoke(run, [str(recipe), 'test'])
    assert LOG.getEffectiveLevel() == logging.INFO


@runner.isolated_filesystem()
def test_work_directory_path():
    """Work directory: -w, --work-directory

    Invariants:
        - Work directory must exist.
        - The path is always absolute.
    """

    # Expected environment
    root = Path.cwd().resolve()
    work_dir = root/'work-dir'
    recipe_path = root/'recipe.yml'
    recipe_name = 'test'

    recipe_path.touch()

    options = ['--work-directory', str(work_dir)]
    arguments = [str(recipe_path), recipe_name]

    # Pre-conditions
    assert not work_dir.exists(), 'Work directory already present'

    # Nonexistent parameter
    with pytest.raises(click.BadParameter):
        run.make_context('test-work_dir-nonexistent', options + arguments)

    # Fine parameters
    work_dir.mkdir()
    ctx = run.make_context('test-work_dir-ok', options + arguments)
    result = Path(ctx.params['work_directory'])
    assert result.is_absolute(), 'Relative work directory path'
    assert result == work_dir, 'Unexpected work directory'


@runner.isolated_filesystem()
def test_custom_file_path():
    """Custom builder/downloader instructions: -c, --custom-file

    Invariants:
        - The file must exists and be readable.
        - The path is always absolute.
    """

    # Expected environment
    root = Path.cwd().resolve()
    custom_file = root/'custom.yml'
    recipe_path = root/'recipe.yml'
    recipe_name = 'test'

    recipe_path.touch()

    options = ['--custom-file', str(custom_file)]
    arguments = [str(recipe_path), recipe_name]

    # Pre-conditions
    assert not custom_file.exists(), 'Custom file already exists'

    # Nonexistent file
    with pytest.raises(click.BadParameter):
        run.make_context('test-custom_file-nonexistent', options + arguments)

    # Unreadable file
    custom_file.touch(mode=0o200)
    with pytest.raises(click.BadParameter):
        run.make_context('test-custom_file-unreadable', options + arguments)

    # Proper result
    custom_file.chmod(0o600)
    ctx = run.make_context('test-custom_file-ok', options + arguments)
    result = Path(ctx.params['custom_file'])
    assert result.is_absolute(), 'Relative custom file path'
    assert result == custom_file, 'Unexpected custom file path'

"""Test argument parsing"""

import os
import logging
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from rpmlb import LOG
from rpmlb.cli import run


@pytest.fixture
def runner():
    r = CliRunner()
    try:
        with r.isolated_filesystem():
            yield r
    finally:
        # Make sure other tests are not affected by the ones with --verbose
        LOG.setLevel(logging.INFO)


@pytest.mark.parametrize('option', ('recipe_file', 'recipe_name', 'build',
                                    'download', 'branch', 'source_directory'))
def test_parse_argv_no_options(tmpdir, option):
    """Tests proper default values of the CLI"""

    RECIPE_FILE = tmpdir.join('ror.yml')
    RECIPE_NAME = 'rh-ror50'

    # Prepare environment
    RECIPE_FILE.write('')

    current_dir = os.path.abspath(os.getcwd())

    expected = {
        'recipe_file': str(RECIPE_FILE),
        'recipe_name': str(RECIPE_NAME),
        'build': 'dummy',
        'download': 'none',
        'branch': None,
        'source_directory': current_dir,
    }

    # Parse the arguments
    with tmpdir.as_cwd():
        argv = list(map(str, [RECIPE_FILE, RECIPE_NAME]))
        args = run.make_context('rpmlb', argv).params

    assert args[option] == expected[option]


@pytest.mark.parametrize('verbose', (True, False))
def test_log_verbosity(runner, verbose):
    """Ensure that the verbosity is set properly on."""

    # Initial state – if the test fails here, the app has changed
    # and the test needs to be adjusted.
    assert LOG.getEffectiveLevel() == logging.INFO

    recipe = Path('recipe.yml')
    recipe.touch()

    verbose_args = ['--verbose'] if verbose else []
    level = logging.DEBUG if verbose else logging.INFO

    runner.invoke(run, verbose_args + [str(recipe), 'test'])
    assert LOG.getEffectiveLevel() == level


@pytest.fixture(params=('work-directory', 'custom-file'))
def path_kind(request):
    return request.param


def path_options_arguments(path_kind):
    """Excepted environment for the path tests"""
    filename = 'custom.yml' if path_kind == 'custom-file' else path_kind

    root = Path.cwd().resolve()
    path = root/filename
    recipe_path = root/'recipe.yml'
    recipe_name = 'test'

    recipe_path.touch()

    options = ['--' + path_kind, str(path)]
    arguments = [str(recipe_path), recipe_name]

    assert not path.exists()

    return path, options, arguments


def test_path_nonexistent(runner, path_kind):
    path, options, arguments = path_options_arguments(path_kind)

    with pytest.raises(click.BadParameter):
        run.make_context('test-{}-nonexistent'.format(path_kind),
                         options + arguments)


def test_path_expected_and_absolute(runner, path_kind):
    path, options, arguments = path_options_arguments(path_kind)

    if path_kind.endswith('directory'):
        path.mkdir()
    else:
        path.touch(mode=0o600)

    ctx = run.make_context('test-{}-ok'.format(path_kind), options + arguments)
    result = Path(ctx.params[path_kind.replace('-', '_')])
    assert result == path
    assert result.is_absolute()


def test_path_bad_permissions(runner, path_kind):
    path, options, arguments = path_options_arguments(path_kind)

    if path_kind.endswith('directory'):
        # unwritable directory
        path.mkdir()
        path.chmod(0o500)
    else:
        # unreadable file
        path.touch(mode=0o200)

    with pytest.raises(click.BadParameter):
        run.make_context('test-{}-bad-permissions'.format(path_kind),
                         options + arguments)

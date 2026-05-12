"""
Tests for Dependencies Downloader

For debug information use:
pytest-3 --log-cli-level debug
"""
import os
import coverage
import yaml
import logging
import importlib
import pytest
import shutil
import subprocess
import sys
from . import context
from kibot.mcpyrate import activate  # noqa: F401
import kibot.dep_downloader as downloader
import kibot.out_compress as compress
import kibot.out_kibom as kibom
from kibot.misc import MISSING_TOOL
import kibot.log as log

cov = coverage.Coverage()
bin_dir = os.path.join('.local', 'share', 'kibot', 'bin')
bin_dir_py = os.path.join('.local', 'bin')
DEP_PYTHON_MODULE_FOOBAR = """
  - name: FooBar
    python_module: true
    role: mandatory
"""


def try_dependency(ctx, caplog, monkeypatch, docstring, name_dep, downloader_name, b_dir, use_wrapper=False):
    with monkeypatch.context() as m:
        # Force the downloader to use the output dir instead of HOME
        home = os.path.abspath(ctx.output_dir)
        m.setenv("HOME", home)
        m.setattr("site.USER_BASE", os.path.join(home, '.local'))
        # Refresh the module with actual dependencies
        mod = importlib.reload(downloader)
        mod.register_deps('test', yaml.safe_load(docstring))
        # Get the dependency
        dep = mod.used_deps['test:'+name_dep]
        # Download it
        cov.load()
        cov.start()
        downloader_func = getattr(mod, downloader_name+'_downloader')
        if use_wrapper:
            dep.downloader = downloader_func
            res, version = mod.try_download_tool_binary(dep)
            if res:
                res, version = mod.check_tool_binary_local(dep)
        else:
            res, version = downloader_func(dep, 'Linux', 'x86_64')
        cov.stop()
        cov.save()
        # We should get the following name:
        logging.debug('Result: {} Version: {}'.format(res, version))
        with open(ctx.get_out_path('caplog.txt'), 'wt') as f:
            f.write(caplog.text)
        full_name = os.path.join(home, b_dir, dep.command)
        assert res == full_name or res == full_name.replace('/bin', '/local/bin')
        # We executed the file


def try_dependency_module(ctx, caplog, monkeypatch, docstring, name_dep, downloader_name):
    # Note: every attempt to install in a chosen dir failed, even when the module was there and in the sys.path the
    # importlib call miserably failed.
    caplog.set_level(logging.DEBUG)
    with monkeypatch.context():
        # Refresh the module with actual dependencies
        mod = importlib.reload(downloader)
        mod.register_deps('test', yaml.safe_load(docstring))
        # Get the dependency
        dep = mod.used_deps['test:'+name_dep]
        logging.info(f"downloader_name: {downloader_name}")
        # Download it
        cov.load()
        cov.start()
        # Python module
        downloader_func = getattr(mod, downloader_name)
        res, version = downloader_func(dep)
        cov.stop()
        cov.save()
        # We should get the following name:
        logging.debug('Result: {} Version: {}'.format(res, version))
        assert res is not None
        assert res.__file__ is not None


@pytest.mark.indep
def test_dep_rar(test_dir, caplog, monkeypatch):
    """ Check the rar_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    try_dependency(ctx, caplog, monkeypatch, compress.__doc__, 'rar', 'rar', bin_dir, use_wrapper=True)


@pytest.mark.slow
@pytest.mark.indep
def test_dep_pytool(test_dir, caplog, monkeypatch):
    """ Check the pytool_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    try_dependency(ctx, caplog, monkeypatch, kibom.__doc__, 'kibom', 'pytool', bin_dir_py)


@pytest.mark.slow
@pytest.mark.indep
def test_dep_rsvg(test_dir, caplog, monkeypatch):
    """ Check the rsvg_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: RSVG\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'rsvg', 'rsvg', bin_dir)


@pytest.mark.indep
def test_dep_git(test_dir, caplog, monkeypatch):
    """ Check the git_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: Git\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'git', 'git', bin_dir)


@pytest.mark.slow
@pytest.mark.indep
def test_dep_gs(test_dir, caplog, monkeypatch):
    """ Check the git_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: Ghostscript\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'ghostscript', 'gs', bin_dir)
    os.remove(os.path.join(ctx.output_dir, bin_dir, 'gs'))


@pytest.mark.xfail(True, reason="URL down", run=True, raises=AssertionError)
# https://imagemagick.org/archive/binaries/magick
# @pytest.mark.skip
@pytest.mark.slow
@pytest.mark.indep
def test_dep_convert(test_dir, caplog, monkeypatch):
    """ Check the convert_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    dep = '  - from: ImageMagick\n    role: mandatory\n'
    try_dependency(ctx, caplog, monkeypatch, downloader.__doc__+dep, 'imagemagick', 'convert', bin_dir)


@pytest.mark.indep
def test_dep_python(test_dir, caplog, monkeypatch):
    """ Check the python_downloader """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    log.debug_level = 10
    # Ensure we don't have engineering-notation
    try:
        import engineering_notation
        logging.debug('Test module is already installed, using pip to uninstall ...')
        cmd = ['pip', 'uninstall', '-y', 'engineering-notation']
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 1 and b'externally-managed-environment' in res.stderr:
            cmd.insert(-1, '--break-system-packages')
            res = subprocess.run(cmd, capture_output=True)
        # Why pip does this???!!!
        dir_name = os.path.dirname(engineering_notation.__file__)
        if os.path.isdir(dir_name):
            logging.debug('Silly pip left things that will allow importing a non-existent module, removing it')
            shutil.rmtree(dir_name)
        logging.debug('Removing engineering_notation from memory')
        del sys.modules["engineering_notation"]
    except Exception as e:
        logging.error(e)
    dep = 'Dependencies:\n  - name: engineering_notation\n    role: mandatory\n    python_module: true\n'
    try_dependency_module(ctx, caplog, monkeypatch, dep, 'engineering_notation', 'check_tool_python')


def try_function(ctx, caplog, monkeypatch, fun_to_test, dep='', dep2=None, disable_download=True):
    log.debug_level = 10
    # Refresh the module with actual dependencies
    mod = importlib.reload(downloader)
    mod.register_deps('test', yaml.safe_load(downloader.__doc__+dep))
    if dep2 is not None:
        mod.register_deps('test2', yaml.safe_load(dep2))
    mod.disable_auto_download = disable_download
    cov.load()
    cov.start()
    res = fun_to_test(mod)
    cov.stop()
    cov.save()
    with open(ctx.get_out_path('caplog.txt'), 'wt') as f:
        f.write(caplog.text)
    return res


def do_test_check_tool_dep_get_ver_fatal(mod):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        mod.check_tool_dep_get_ver('test', 'foobar', fatal=True)
    return pytest_wrapped_e


@pytest.mark.indep
def test_check_tool_dep_get_ver_1(test_dir, caplog, monkeypatch):
    """ Check for missing stuff in check_tool_dep_get_ver
        Also checks show_roles, get_version and do_log_error """
    # Create a context to get an output directory
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    dep = """
  - name: FooBar
    version: 1.3.0.4
    extra_deb: ['foobar-extra-debian', 'deb2']
    arch: foobar-arch (AUR)
    extra_arch: ['foobar-extra-arch', 'aur2']
    command: foobar
    role: Do this and this
"""
    pytest_wrapped_e = try_function(ctx, caplog, monkeypatch, do_test_check_tool_dep_get_ver_fatal, dep=dep)
    # Check the messages
    assert "Missing `foobar` command (FooBar), install it" in caplog.text
    assert "AUR package: foobar-arch (AUR)" in caplog.text
    assert "Recommended extra Arch packages: foobar-extra-arch aur2" in caplog.text
    assert "Recommended extra Debian packages: foobar-extra-debian deb2" in caplog.text
    assert "Used to do this and this (v1.3.0.4)" in caplog.text
    assert "This is not an official package" in caplog.text
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == MISSING_TOOL


def do_check_tool_python(mod):
    mod.python_downloader = lambda x: True
    return mod.check_tool_python(mod.used_deps['test:foobar'])


@pytest.mark.indep
def test_check_tool_python_1(test_dir, caplog, monkeypatch):
    """ Download disabled case """
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    try_function(ctx, caplog, monkeypatch, do_check_tool_python, dep=DEP_PYTHON_MODULE_FOOBAR)


@pytest.mark.indep
def test_check_tool_python_2(test_dir, caplog, monkeypatch):
    """ Download enabled, but fails """
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    try_function(ctx, caplog, monkeypatch, do_check_tool_python, dep=DEP_PYTHON_MODULE_FOOBAR, disable_download=False)

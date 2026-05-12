"""
Tests for KiCad configuration load

Is quite hard to test this without messing with the system.
For this reason this test is more 'traditional' and uses pytest tools to
pretend we are under certain situations.
I like the other strategy: test the whole script doing something real.
But here the monkeypatch and raises tools make a huge difference.

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import pytest
import coverage
import logging
import sysconfig
from subprocess import run, STDOUT, PIPE
from . import context
from kibot.kicad.config import KiConf
from kibot.gs import GS


cov = coverage.Coverage()
_real_posix_prefix = None


@pytest.mark.skipif(context.ki6(), reason="sym-lib-table used by KiCad 5")
def test_kicad_conf_bad_sym_lib_table(test_dir):
    """ Check various problems in the sym-lib-table file """
    sch = 'sym-lib-table_errors/kibom-test'
    ctx = context.TestContextSCH(test_dir, sch, 'int_bom_simple_csv')
    ctx.run(extra_debug=True)
    # ctx.search_err('Malformed lib entry') Now the lack of descr isn't an error
    ctx.search_err(r'Unable to expand .?BOGUS.? in')
    ctx.search_err(r'unnamed LibAlias')
    ctx.clean_up()


def test_kicad_conf_no_instance():
    """ Check we can't create a KiConf instance """
    with context.cover_it(cov):
        with pytest.raises(AssertionError) as pytest_wrapped_e:
            o = KiConf()  # noqa: F841
    assert pytest_wrapped_e.type == AssertionError
    assert str(pytest_wrapped_e.value) == 'KiConf is fully static, no instances allowed'


def check_load_conf(dir='kicad', fail=False, catch_conf_error=False, no_conf_path=False, patch_get_path=False):
    cmd = ['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kiconf_init.py')]
    if no_conf_path:
        cmd.append('--no_conf_path')
    if patch_get_path:
        cmd.append('--patch_get_path')
    res = run(cmd, stdout=PIPE, stderr=STDOUT).stdout.decode()
    logging.debug(res)
    ref = 'Reading KiCad config from `tests/data/'+dir  # +'/kicad_common`'
    if fail:
        ref = 'Unable to find KiCad configuration file'
    assert ref in res, res
    return res


def test_kicad_conf_user(monkeypatch):
    """ Check we can load the KiCad configuration from $KICAD_CONFIG_HOME """
    GS.debug_level = 2
    with monkeypatch.context() as m:
        m.setenv("KICAD_CONFIG_HOME", 'tests/data/kicad_ok')
        res = check_load_conf(dir='kicad_ok')
    assert 'KICAD_TEMPLATE_DIR="/usr/share/kicad/template_test"' in res, res


def test_kicad_conf_xdg(monkeypatch):
    """ Check we can load the KiCad configuration from $XDG_CONFIG_HOME/kicad """
    with monkeypatch.context() as m:
        m.setenv("XDG_CONFIG_HOME", 'tests/data')
        res = check_load_conf()
    msg = 'KiCad config without EnvironmentVariables section'
    if context.ki6():
        msg = 'KiCad config without environment.vars section'
    assert msg in res, res


def test_kicad_conf_guess_libs(monkeypatch):
    """ Check no HOME and fail to load kicad_common.
        Also check we correctly guess the libs dir. """
    res = check_load_conf(fail=True, no_conf_path=True)
    if context.ki10():
        name = "KICAD10_SYMBOL_DIR"
    elif context.ki9():
        name = "KICAD9_SYMBOL_DIR"
    elif context.ki8():
        name = "KICAD8_SYMBOL_DIR"
    elif context.ki7():
        name = "KICAD7_SYMBOL_DIR"
    elif context.ki6():
        name = "KICAD6_SYMBOL_DIR"
    else:
        name = "KICAD_SYMBOL_DIR"
    assert ('Using {}="/usr/share/kicad/'.format(name) in res or
            'Using {}="/usr/share/kicad-nightly/'.format(name) in res), res


def test_kicad_conf_lib_env(monkeypatch):
    """ Check we can use KICAD_SYMBOL_DIR as fallback """
    if context.ki8():
        name = "KICAD8_SYMBOL_DIR"
    elif context.ki7():
        name = "KICAD7_SYMBOL_DIR"
    elif context.ki6():
        name = "KICAD6_SYMBOL_DIR"
    else:
        name = "KICAD_SYMBOL_DIR"
    with monkeypatch.context() as m:
        m.setenv(name, 'tests')
        res = check_load_conf(fail=True, no_conf_path=True)
    assert 'Using {}="tests"'.format(name) in res, res


def test_kicad_conf_sym_err_1(monkeypatch):
    """ Test broken sym-lib-table, no signature """
    GS.debug_level = 2
    with monkeypatch.context() as m:
        m.setenv("KICAD_CONFIG_HOME", 'tests/data/kicad_err_1')
        res = check_load_conf(dir='kicad_err_1', catch_conf_error=True)
    assert "Too many closing brackets. Expected no character left in the sexp" in res, res


def test_kicad_conf_sym_err_2(monkeypatch):
    """ Test broken sym-lib-table, wrong entry """
    GS.debug_level = 2
    with monkeypatch.context() as m:
        m.setenv("KICAD_CONFIG_HOME", 'tests/data/kicad_err_2')
        res = check_load_conf(dir='kicad_err_2', catch_conf_error=True)
    assert "Unknown lib table entry" in res, res


def mocked_get_path_1(name, scheme):
    """ Pretend the system libs are the user ones.
        Disable the system libs. """
    if name == 'data':
        if scheme == 'posix_user':
            return _real_posix_prefix
        elif scheme == 'posix_prefix':
            return ''
    return sysconfig.get_path(name, scheme)


def test_kicad_conf_local_conf(monkeypatch):
    """ Test if we can use the 'posix_user' """
    global _real_posix_prefix
    _real_posix_prefix = sysconfig.get_path('data', 'posix_prefix')
    with monkeypatch.context() as m:
        m.setattr("sysconfig.get_path", mocked_get_path_1)
        with context.cover_it(cov):
            assert (KiConf.guess_symbol_dir() == '/usr/share/kicad/library' or
                    KiConf.guess_symbol_dir() == '/usr/share/kicad/symbols' or
                    KiConf.guess_symbol_dir() == '/usr/share/kicad-nightly/library' or
                    KiConf.guess_symbol_dir() == '/usr/share/kicad-nightly/symbols')


def test_kicad_conf_no_conf():
    """ Test a complete fail to find libs """
    res = check_load_conf(fail=True, no_conf_path=True, patch_get_path=True)
    assert 'Unable to find KiCad libraries' in res, res


def test_config_redirect(monkeypatch):
    """ Test bizarre KICAD_CONFIG_HOME inside kicad_common """
    with monkeypatch.context() as m:
        m.setenv("KICAD_CONFIG_HOME", 'tests/data/config_redirect')
        res = check_load_conf(dir='config_redirect')
    assert 'Reading KiCad config from `tests/data/config_redirect/' in res, res
    assert 'Redirecting symbols lib table to /usr/share/kicad/template' in res, res

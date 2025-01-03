import os
import sys
import shutil
import tempfile
import logging
import subprocess
import re
import csv
from contextlib import contextmanager
from glob import glob
from pty import openpty
import xml.etree.ElementTree as ET
prev_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# py-test inserts things at the beginning, so we could end loading an installed copy of KiBot
if sys.path[0] != prev_dir:
    try:
        sys.path.remove(prev_dir)
    except ValueError:
        pass
    sys.path.insert(0, prev_dir)
from kibot.misc import (error_level_to_name)

COVERAGE_SCRIPT = 'python3-coverage'
if shutil.which(COVERAGE_SCRIPT) is None:
    COVERAGE_SCRIPT = 'coverage3'
    assert shutil.which(COVERAGE_SCRIPT) is not None
KICAD_PCB_EXT = '.kicad_pcb'
KICAD_VERSION_5_1_7 = 5001007
KICAD_VERSION_5_99 = 5099000
KICAD_VERSION_6_0_0 = 6000000
KICAD_VERSION_7_0_0 = 7000000
KICAD_VERSION_7_0_3 = 7000003
KICAD_VERSION_7_0_6 = 7000006
KICAD_VERSION_7_0_7 = 7000007
KICAD_VERSION_7_0_10 = 7000010
KICAD_VERSION_7_0_11 = 7000011
KICAD_VERSION_8_0_0 = 7099000
MODE_SCH = 1
MODE_PCB = 0
# Defined as True to collect real world queries
ADD_QUERY_TO_KNOWN = False

ng_ver = os.environ.get('KIAUS_USE_NIGHTLY')
if ng_ver:
    # Path to the Python module
    sys.path.insert(0, '/usr/lib/kicad-nightly/lib/python3/dist-packages')
import pcbnew
build_version = pcbnew.GetBuildVersion()
m = re.search(r'(\d+)\.(\d+)\.(\d+)', build_version)
logging.debug(build_version)
kicad_major = int(m.group(1))
kicad_minor = int(m.group(2))
kicad_patch = int(m.group(3))
kicad_version = kicad_major*1000000+kicad_minor*1000+kicad_patch
if kicad_version >= KICAD_VERSION_5_99:
    km = kicad_major+(0 if kicad_minor < 99 else 1)
    if km > 8:
        km = 8
    BOARDS_DIR = '../board_samples/kicad_'+str(km)
    if kicad_version >= KICAD_VERSION_8_0_0:
        REF_DIR = 'tests/reference/8_0_0'
    elif kicad_version >= KICAD_VERSION_7_0_11 and 'rc' in build_version:
        REF_DIR = 'tests/reference/stable_nightly'
    elif kicad_version >= KICAD_VERSION_7_0_10:
        REF_DIR = 'tests/reference/7_0_10'
    elif kicad_version >= KICAD_VERSION_7_0_6:
        REF_DIR = 'tests/reference/7_0_6'
    elif kicad_version >= KICAD_VERSION_7_0_3:
        REF_DIR = 'tests/reference/7_0_3'
    elif kicad_version >= KICAD_VERSION_7_0_0:
        REF_DIR = 'tests/reference/7_0_0'
    else:
        REF_DIR = 'tests/reference/6_0_8'
    logging.debug('Reference dir: '+REF_DIR)
    KICAD_SCH_EXT = '.kicad_sch'
    # Now these layers can be renamed.
    # KiCad 6 takes the freedom to give them more descriptive names ...
    DEF_ADHES = 'Adhesive'
    DEF_CRTYD = 'Courtyard'
    DEF_SILKS = 'Silkscreen'
    DEF_CMTSU = 'User_Comments'
    DEF_DWGSU = 'User_Drawings'
    DEF_ECO1U = 'User_Eco1'
    DEF_ECO2U = 'User_Eco2'
    PRO_EXT = '.kicad_pro'
else:
    BOARDS_DIR = '../board_samples/kicad_5'
    KICAD_SCH_EXT = '.sch'
    DEF_ADHES = 'Adhes'
    DEF_CRTYD = 'CrtYd'
    DEF_SILKS = 'SilkS'
    DEF_CMTSU = 'Cmts_User'
    DEF_DWGSU = 'Dwgs_User'
    DEF_ECO1U = 'Eco1_User'
    DEF_ECO2U = 'Eco2_User'
    if kicad_version >= KICAD_VERSION_5_1_7:
        # 5.1.8 uses the same references as 5.1.7
        REF_DIR = 'tests/reference/5_1_7'
    else:
        REF_DIR = 'tests/reference/5_1_6'
    PRO_EXT = '.pro'
logging.debug('Detected KiCad v{}.{}.{} ({})'.format(kicad_major, kicad_minor, kicad_patch, kicad_version))


def ki8():
    return kicad_version >= KICAD_VERSION_8_0_0


def ki7():
    return kicad_version >= KICAD_VERSION_7_0_0


def ki6():
    return kicad_version >= KICAD_VERSION_5_99


def ki5():
    return kicad_version < KICAD_VERSION_5_99


def quote(s):
    return '"'+s+'"'


def usable_cmd(cmd):
    return ' '.join(cmd)


def move_existant(name):
    if not os.path.isfile(name):
        return
    for n in range(9):
        new_name = name+f'_{n+1}'
        if not os.path.isfile(new_name):
            break
    os.rename(name, new_name)


@contextmanager
def cover_it(cov):
    # Start coverage
    cov.load()
    cov.start()
    yield
    # Stop coverage
    cov.stop()
    cov.save()


class TestContext(object):

    def __init__(self, test_dir, board_name, yaml_name, sub_dir='', yaml_compressed=False, add_cfg_kmajor=False,
                 test_name=None, relaxed=False):
        if test_name is None:
            test_name = sys._getframe(1).f_code.co_name
        if test_name.startswith('test_'):
            test_name = test_name[5:]
        self.kicad_version = kicad_version
        if add_cfg_kmajor:
            major = kicad_major
            if kicad_minor == 99:
                # KiCad 5.99 is 6.0.0 alpha
                major = 6
            yaml_name += str(major)
        if not hasattr(self, 'mode'):
            # We are using PCBs
            self.mode = MODE_PCB
        # The name used for the test output dirs and other logging
        self.test_name = test_name
        # The name of the PCB board file
        self.board_name = board_name
        # The actual board file that will be loaded
        self._get_board_file(relaxed=relaxed)
        # The YAML file we'll use
        self._get_yaml_name(yaml_name, yaml_compressed)
        # The actual output dir for this run
        self._set_up_output_dir(test_dir)
        # Where are we expecting to get the outputs (inside test_name)
        self.sub_dir = sub_dir
        # stdout and stderr from the run
        self.out = None
        self.err = None
        self.proc = None

    def get_board_dir(self, file=None):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        if file is None:
            return os.path.join(this_dir, BOARDS_DIR)
        return os.path.join(this_dir, BOARDS_DIR, file)

    def _get_board_file(self, relaxed=False):
        self.board_file = os.path.abspath(os.path.join(self.get_board_dir(), self.board_name + KICAD_PCB_EXT))
        self.sch_file = os.path.abspath(os.path.join(self.get_board_dir(), self.board_name + KICAD_SCH_EXT))
        logging.info('KiCad file: '+self.board_file)
        if not relaxed:
            if self.mode == MODE_PCB:
                assert os.path.isfile(self.board_file), self.board_file
            else:
                assert os.path.isfile(self.sch_file), self.sch_file

    def _get_yaml_dir(self):
        this_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(this_dir, '../yaml_samples')

    def _get_yaml_name(self, name, yaml_compressed):
        if name.endswith('.kibot.yaml'):
            self.yaml_file = name
        else:
            self.yaml_file = os.path.abspath(os.path.join(self._get_yaml_dir(), name+'.kibot.yaml'))
        if yaml_compressed:
            self.yaml_file += '.gz'
        if not os.path.isfile(self.yaml_file):
            self.yaml_file = self.yaml_file.replace('.kibot.', '.kiplot.')
        logging.info('YAML file: '+self.yaml_file)
        assert os.path.isfile(self.yaml_file), self.yaml_file

    def _set_up_output_dir(self, test_dir):
        if test_dir:
            self.output_dir = os.path.join(test_dir, self.test_name)
            os.makedirs(self.output_dir, exist_ok=True)
            self._del_dir_after = False
        else:
            # create a tmp dir
            self.output_dir = tempfile.mkdtemp(prefix='tmp-kibot-'+self.test_name+'-')
            self._del_dir_after = True
        logging.info('Output dir: '+self.output_dir)

    def clean_up(self, keep_project=False):
        logging.debug('Clean-up')
        if self._del_dir_after:
            logging.debug('Removing dir')
            shutil.rmtree(self.output_dir)
        # We don't have a project, and we don't want one
        pro = os.path.join(self.get_board_dir(), self.board_name+PRO_EXT)
        if os.path.isfile(pro) and not keep_project:
            os.remove(pro)
            if PRO_EXT == '.kicad_pro':
                prl = os.path.join(self.get_board_dir(), self.board_name+'.kicad_prl')
                if os.path.isfile(prl):
                    os.remove(prl)
        # We don't have a footprint cache, and we don't want one
        fp_cache = os.path.join(self.get_board_dir(), 'fp-info-cache')
        if os.path.isfile(fp_cache):
            os.remove(fp_cache)

    def get_out_path(self, filename, sub=False):
        return os.path.join(self.output_dir, filename) if not sub else os.path.join(self.output_dir, self.sub_dir, filename)

    def get_gerber_job_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-job.gbrjob')

    def get_gerber_filename(self, layer_slug, ext='.gbr'):
        return os.path.join(self.sub_dir, self.board_name+'-'+layer_slug+ext)

    def get_pos_top_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-top_pos.pos')

    def get_pos_bot_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-bottom_pos.pos')

    def get_pos_both_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-both_pos.pos')

    def get_pos_top_csv_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-top_pos.csv')

    def get_pos_bot_csv_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-bottom_pos.csv')

    def get_pos_both_csv_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-both_pos.csv')

    def get_pth_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-PTH.drl')

    def get_pth_gbr_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-PTH-drl.gbr')

    def get_pth_pdf_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-PTH-drl_map.pdf')

    def get_pth_csv_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-(L1 - L4)_drill_table.csv')

    def get_f1_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-front-in1.drl')

    def get_f1_gbr_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-front-in1-drl.gbr')

    def get_f1_pdf_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-front-in1-drl_map.pdf')

    def get_f1_csv_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-(L1 - L2)_drill_table.csv')

    def get_12_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-in1-in2.drl')

    def get_12_gbr_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-in1-in2-drl.gbr')

    def get_12_pdf_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-in1-in2-drl_map.pdf')

    def get_12_csv_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-(L2 - L3)_drill_table.csv')

    def get_npth_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-NPTH.drl')

    def get_npth_gbr_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-NPTH-drl.gbr')

    def get_npth_pdf_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-NPTH-drl_map.pdf')

    def get_npth_csv_drl_filename(self):
        return os.path.join(self.sub_dir, self.board_name+'-(L1 - L4)_NPTH_drill_table.csv')

    def expect_out_file(self, filename, sub=False):
        if isinstance(filename, str):
            filename = [filename]
        files = []
        for f in filename:
            file = self.get_out_path(f, sub)
            assert os.path.isfile(file), file
            assert os.path.getsize(file) > 0
            logging.debug(f+' OK')
            files.append(file)
        return files[0] if len(files) == 1 else files

    def expect_out_file_d(self, filename):
        if isinstance(filename, str):
            filename = [filename]
        return self.expect_out_file([os.path.join(self.sub_dir, f) for f in filename])

    def dont_expect_out_file(self, filename):
        file = self.get_out_path(filename)
        assert not os.path.isfile(file)

    def create_dummy_out_file(self, filename):
        file = self.get_out_path(filename)
        with open(file, 'w') as f:
            f.write('Dummy file\n')

    def do_run(self, cmd, ret_val=None, use_a_tty=False, chdir_out=False):
        cmd_base = [COVERAGE_SCRIPT, 'run']
        if chdir_out:
            cwd = os.getcwd()
            cmd_base.append('--rcfile='+os.path.join(cwd, '.coveragerc'))
            os.environ['COVERAGE_FILE'] = os.path.join(cwd, '.coverage')
        cmd = cmd_base+cmd
        logging.debug(usable_cmd(cmd))
        out_filename = self.get_out_path('output.txt')
        err_filename = self.get_out_path('error.txt')
        if use_a_tty:
            # This is used to test the coloured logs, we need stderr to be a TTY
            master, slave = openpty()
            f_err = slave
            f_out = slave
        else:
            move_existant(out_filename)
            move_existant(err_filename)
            # Redirect stdout and stderr to files
            f_out = os.open(out_filename, os.O_RDWR | os.O_CREAT)
            f_err = os.open(err_filename, os.O_RDWR | os.O_CREAT)
        # Run the process
        if chdir_out:
            cwd = os.getcwd()
            os.chdir(self.output_dir)
        process = subprocess.Popen(cmd, stdout=f_out, stderr=f_err)
        if chdir_out:
            os.chdir(cwd)
            del os.environ['COVERAGE_FILE']
        ret_code = process.wait()
        logging.debug('ret_code '+str(ret_code))
        if use_a_tty:
            self.err = os.read(master, 10000)
            self.err = self.err.decode()
            self.out = self.err
        exp_ret = 0 if ret_val is None else ret_val
        assert ret_code == exp_ret, 'ret_code: {} ({}) expected {} ({})'.format(ret_code, error_level_to_name[ret_code],
                                                                                exp_ret, error_level_to_name[exp_ret])
        if use_a_tty:
            os.close(master)
            os.close(slave)
            with open(out_filename, 'w') as f:
                f.write(self.out)
            with open(err_filename, 'w') as f:
                f.write(self.out)
        else:
            # Read stdout
            os.lseek(f_out, 0, os.SEEK_SET)
            self.out = os.read(f_out, 10000000)
            os.close(f_out)
            self.out = self.out.decode()
            # Read stderr
            os.lseek(f_err, 0, os.SEEK_SET)
            self.err = os.read(f_err, 10000000)
            os.close(f_err)
            self.err = self.err.decode()

    def run_command(self, cmd, chdir_out=False):
        if chdir_out:
            cwd = os.getcwd()
            os.chdir(self.output_dir if isinstance(chdir_out, bool) else chdir_out)
        logging.debug('Executing: '+usable_cmd(cmd))
        try:
            res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error('Running {} returned {}'.format(e.cmd, e.returncode))
            if e.stdout:
                logging.debug('- Output from command: '+e.stdout.decode())
            raise
        finally:
            if chdir_out:
                os.chdir(cwd)
        if res.stdout:
            logging.debug('- Output from command: '+res.stdout.decode())
        return res.stdout.decode().rstrip()

    def run(self, ret_val=None, extra=None, use_a_tty=False, filename=None, no_out_dir=False, no_board_file=False,
            no_yaml_file=False, chdir_out=False, no_verbose=False, extra_debug=False, do_locale=False, kicost=False):
        logging.debug('Running '+self.test_name)
        # Change the command to be local and add the board and output arguments
        cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../../src/kibot')]
        if not no_verbose:
            # One is enough, 2 can generate tons of data when loading libs
            cmd.append('-v')
            if extra_debug:
                cmd.append('-vvv')
        if not no_board_file:
            if self.mode == MODE_PCB:
                cmd = cmd+['-b', filename if filename else self.board_file]
            else:
                cmd = cmd+['-e', filename if filename else self.sch_file]
        if not no_yaml_file:
            cmd = cmd+['-c', self.yaml_file]
        if not no_out_dir:
            cmd = cmd+['-d', self.output_dir]
        if extra is not None:
            cmd = cmd+extra
        # Do we need a custom locale?
        old_LOCPATH = None
        old_LANG = None
        if do_locale:
            # Setup an Spanish for Argentina using UTF-8 locale
            old_LOCPATH = os.environ.get('LOCPATH')
            old_LANG = os.environ.get('LANG')
            os.environ['LOCPATH'] = os.path.abspath('tests/data')
            os.environ['LANG'] = do_locale
            logging.debug('LOCPATH='+os.environ['LOCPATH'])
            logging.debug('LANG='+os.environ['LANG'])
        # KiCost fake environment setup
        if kicost:
            # Always fake the currency rates
            os.environ['KICOST_CURRENCY_RATES'] = 'tests/data/currency_rates.xml'
            if ADD_QUERY_TO_KNOWN:
                queries_file = 'tests/data/kitspace_queries.txt'
                os.environ['KICOST_LOG_HTTP'] = queries_file
                with open(queries_file, 'at') as f:
                    f.write('# ' + self.board_name + '\n')
                server = None
            else:
                os.environ['KICOST_KITSPACE_URL'] = 'http://localhost:8000'
                os.environ['KIBOT_EASYEDA_API'] = 'http://localhost:8000/api/{lcsc_id}'
                os.environ['KIBOT_EASYEDA_MODEL'] = 'http://localhost:8000/model/{uuid}'
                os.environ['KIBOT_EASYEDA_STEP'] = 'http://localhost:8000/step/{uuid}'

                f_o = open(self.get_out_path('server_stdout.txt'), 'at')
                f_e = open(self.get_out_path('server_stderr.txt'), 'at')
                server = subprocess.Popen('./tests/utils/dummy-web-server.py', stdout=f_o, stderr=f_e)
        try:
            self.do_run(cmd, ret_val, use_a_tty, chdir_out)
        finally:
            # Always kill the fake web server
            if kicost and server is not None:
                server.terminate()
                f_o.close()
                f_e.close()
        # Do we need to restore the locale?
        if do_locale:
            if old_LOCPATH:
                os.environ['LOCPATH'] = old_LOCPATH
            else:
                del os.environ['LOCPATH']
            if old_LANG:
                os.environ['LANG'] = old_LANG
            else:
                del os.environ['LANG']

    def _search_txt(self, text, msgs, where, invert=False):
        if isinstance(text, list):
            res = []
            for t in text:
                m = re.search(t, msgs, re.MULTILINE)
                if invert:
                    assert m is None, t
                    logging.debug(f'{where} no match: `{t}` OK')
                else:
                    assert m is not None, t
                    logging.debug(f'{where} match: `{t}` (`{m.group(0)}`) OK')
                    res.append(m)
            return res
        m = re.search(text, msgs, re.MULTILINE)
        if invert:
            assert m is None, text
            logging.debug(f'{where} no match: `{text}` OK')
        else:
            assert m is not None, text
            logging.debug(f'{where} match: `{text}` (`{m.group(0)}`) OK')
        return m

    def search_out(self, text, invert=False):
        return self._search_txt(text, self.out, 'output', invert)

    def search_err(self, text, invert=False):
        return self._search_txt(text, self.err, 'error', invert)

    def search_in_file(self, file, texts, sub=False):
        logging.debug('Searching in "'+file+'" output')
        with open(self.get_out_path(file, sub=sub)) as f:
            txt = f.read()
        res = []
        for t in texts:
            msg = '- r"'+t+'"'
            m = re.search(t, txt, re.MULTILINE)
            assert m, msg
            logging.debug(msg+' OK')
            # logging.debug(' '+m.group(0))
            res.append(m.groups())
        return res

    def search_in_file_d(self, file, texts):
        if isinstance(texts, str):
            texts = [texts]
        return self.search_in_file(os.path.join(self.sub_dir, file), texts)

    def search_not_in_file(self, file, texts):
        logging.debug('Searching not in "'+file+'" output')
        with open(self.get_out_path(file)) as f:
            txt = f.read()
        for t in texts:
            msg = '- r"'+t+'"'
            m = re.search(t, txt, re.MULTILINE)
            assert m is None, msg
            logging.debug(msg+' OK')
            # logging.debug(' '+m.group(0))

    def search_not_in_file_d(self, file, texts):
        return self.search_not_in_file(os.path.join(self.sub_dir, file), texts)

    def compare_image(self, image, reference=None, diff='diff.png', ref_out_dir=False, fuzz='5%', tol=0, height='87%',
                      off_y='0', sub=False, trim=False, fix_here=True):
        """ For images and single page PDFs """
        if reference is None:
            reference = image
        if ref_out_dir:
            reference = self.get_out_path(reference)
        else:
            reference = os.path.join(REF_DIR, reference)
        full_ref = reference
        image = self.get_out_path(image, sub)
        full_img = image
        png_ref = None
        if reference[-3:] == 'svg':
            png_ref = reference[:-3]+'png'
            cmd = ['rsvg-convert', '-b', '#FFFFFF', '-h', '2160', '-o', png_ref, reference]
            logging.debug('Converting reference to PNG with: '+usable_cmd(cmd))
            subprocess.check_call(cmd)
            reference = png_ref
            assert os.path.isfile(png_ref)
        png_image = None
        if image[-3:] == 'svg':
            png_image = image[:-3]+'png'
            cmd = ['rsvg-convert', '-b', '#FFFFFF', '-h', '2160', '-o', png_image, image]
            logging.debug('Converting result image to PNG with: '+usable_cmd(cmd))
            subprocess.check_call(cmd)
            image = png_image
            assert os.path.isfile(png_image)
        if trim:
            cmd = ['convert', image, '-trim', image]
            subprocess.run(cmd)
        cmd = ['compare',
               # Tolerate 5 % error in color
               '-fuzz', fuzz,
               # Count how many pixels differ
               '-metric', 'AE',
               image,
               reference,
               # Avoid the part where KiCad version is printed
               '-crop', '100%x'+height+'+0+'+off_y, '+repage',
               '-colorspace', 'RGB',
               self.get_out_path(diff)]
        logging.debug('Comparing images with: '+usable_cmd(cmd))
        res = subprocess.run(cmd, stderr=subprocess.STDOUT, check=False, stdout=subprocess.PIPE).stdout
        # m = re.match(r'([\d\.e-]+) \(([\d\.e-]+)\)', res.decode())
        # assert m
        # logging.debug('MSE={} ({})'.format(m.group(1), m.group(2)))
        s = res.decode()
        # Remove error messages generated by KiCad 7 plotted PDFs
        s = re.sub(r'^\s+\*+.*', '', s, count=0, flags=re.M)
        s = re.sub(r'^\s+Output may be incorrect.*', '', s, count=0, flags=re.M)
        s = s.strip()
        ae = int(s)
        logging.debug('AE=%d' % ae)
        if png_ref:
            os.remove(png_ref)
        if png_image:
            os.remove(png_image)
        if ae > tol and fix_here and os.environ.get('KIBOT_COPY_REF') == '1':
            logging.error(f'cp {full_img} {full_ref}')
            shutil.copy2(full_img, full_ref)
        assert ae <= tol

    def compare_pdf(self, gen, reference=None, diff='diff-{}.png', height='87%', off_y='0', tol=0):
        """ For multi-page PDFs """
        if reference is None:
            reference = gen
        logging.debug('Comparing PDFs: '+gen+' vs '+reference)
        # Split the reference
        logging.debug('Splitting '+reference)
        full_ref_name = os.path.join(REF_DIR, reference)
        cmd = ['convert', '-density', '150',
               full_ref_name,
               # Avoid the transparency, not repeatable across KiCad releases
               '-background', 'white', '-alpha', 'background', '-alpha', 'off',
               self.get_out_path('ref-%d.png')]
        logging.debug(full_ref_name)
        subprocess.check_call(cmd)
        # Split the generated
        logging.debug('Splitting '+gen)
        full_gen_name = self.get_out_path(gen)
        cmd = ['convert', '-density', '150',
               full_gen_name,
               # Avoid the transparency, not repeatable across KiCad releases
               '-background', 'white', '-alpha', 'background', '-alpha', 'off',
               self.get_out_path('gen-%d.png')]
        subprocess.check_call(cmd)
        # Check number of pages
        ref_pages = glob(self.get_out_path('ref-*.png'))
        gen_pages = glob(self.get_out_path('gen-*.png'))
        logging.debug('Pages {} vs {}'.format(len(gen_pages), len(ref_pages)))
        assert len(ref_pages) == len(gen_pages)
        # Compare each page
        try:
            for page in range(len(ref_pages)):
                self.compare_image('gen-'+str(page)+'.png', 'ref-'+str(page)+'.png', diff.format(page), ref_out_dir=True,
                                   height=height, off_y=off_y, tol=tol, fix_here=False)
        except AssertionError:
            if os.environ.get('KIBOT_COPY_REF') == '1':
                logging.error(f'cp {full_gen_name} {full_ref_name}')
                shutil.copy2(full_gen_name, full_ref_name)
            raise

    def compare_txt(self, text, reference=None, diff='diff.txt'):
        if reference is None:
            reference = text
        full_ref_name = os.path.join(REF_DIR, reference)
        full_text_name = self.get_out_path(text)
        cmd = ['/bin/sh', '-c', 'diff -uBb '+full_ref_name+' '+full_text_name+' > '+self.get_out_path(diff)]
        logging.debug('Comparing texts with: '+usable_cmd(cmd))
        res = subprocess.call(cmd)
        if res and os.environ.get('KIBOT_COPY_REF') == '1':
            logging.error(f'cp {full_text_name} {full_ref_name}')
            shutil.copy2(full_text_name, full_ref_name)
        assert res == 0, res

    def compare_txt_d(self, text, reference=None, diff='diff.txt'):
        if reference is None:
            reference = text
        text = os.path.join(self.sub_dir, text)
        diff = os.path.join(self.sub_dir, diff)
        self.compare_txt(text, reference, diff)

    def compare_txt_d2(self, text, reference=None, diff='diff.txt'):
        if reference is None:
            reference = text
        reference = os.path.join(self.sub_dir, reference)
        self.compare_txt_d(text, reference, diff)

    def filter_txt(self, file, pattern, repl):
        fname = self.get_out_path(file)
        with open(fname) as f:
            txt = f.read()
        with open(fname, 'w') as f:
            f.write(re.sub(pattern, repl, txt))

    def get_pdf_size(self, file):
        cmd = ['pdfinfo', file]
        logging.debug('Analyzing PDF size: '+usable_cmd(cmd))
        res = subprocess.run(cmd, stderr=subprocess.STDOUT, check=True, stdout=subprocess.PIPE).stdout.decode()
        m = re.search(r'Page size:\s+([\d\.]+) x ([\d\.]+) pts', res)
        assert m is not None, res
        return float(m.group(1))/72.0*25.4, float(m.group(2))/72.0*25.4

    def expect_gerber_flash_at(self, file, res, pos):
        """
        Check for a gerber flash at a given point
        (it's hard to check that aperture is right without a real gerber parser
        """
        if res == 6:  # 4.6
            mult = 1000000
        else:  # 4.5
            mult = 100000
        repat = r'^X{x}Y{y}D03\*$'.format(x=int(pos[0]*mult), y=int(pos[1]*mult))
        self.search_in_file(file, [repat])
        logging.debug("Gerber flash found: "+repat)

    def expect_gerber_has_apertures(self, file, ap_list):
        ap_matches = []
        for ap in ap_list:
            # find the circular aperture for the outline
            ap_matches.append(r'%AD(.*)'+ap+r'\*%')
        grps = self.search_in_file(file, ap_matches)
        aps = []
        for grp in grps:
            ap_no = grp[0]
            assert ap_no is not None
            # apertures from D10 to D999
            assert len(ap_no) in [2, 3]
            aps.append(ap_no)
        logging.debug("Found apertures {}".format(aps))
        return aps

    def load_csv(self, filename, delimiter=','):
        rows = []
        with open(self.expect_out_file(os.path.join(self.sub_dir, filename))) as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            header = next(reader)
            for r in reader:
                if not r:
                    break
                rows.append(r)
            # Collect info
            info = []
            for r in reader:
                if r:
                    info.append(r)
        return rows, header, info

    def load_hrtxt(self, filename):
        nm = self.expect_out_file(os.path.join(self.sub_dir, filename))
        nm_csv = nm.replace('.txt', '.csv')
        with open(nm) as f:
            with open(nm_csv, 'wt') as d:
                for ln in f:
                    if ln.startswith('I---'):
                        continue
                    if ln[0] == 'I':
                        ln = ln[1:-2]
                    ln = ln.strip()
                    d.write(','.join(re.split(r'\s*I', ln)))
                    d.write('\n')
        return self.load_csv(filename.replace('.txt', '.csv'))

    def load_html(self, filename):
        file = self.expect_out_file(os.path.join(self.sub_dir, filename))
        with open(file) as f:
            html = f.read()
        rows = []
        headers = []
        sh_head = {}
        for cl, body in re.findall(r'<table class="(.*?)">((?:\s+.*?)+)</table>', html, re.MULTILINE):
            if cl == 'head-table':
                # Extract logo
                m = re.search(r'<img src="((.*?\n?)+)" alt="Logo"', body, re.MULTILINE)
                if m:
                    sh_head['logo'] = m.group(1)
                # Extract title
                m = re.search(r'<div class="title">(.*?)</div>', body)
                if m:
                    sh_head['title'] = m.group(1)
                # Extract PCB info
                m = re.search(r'<td class="cell-info">((?:\s+.*?)+)</td>', body, re.MULTILINE)
                if m:
                    info = m.group(1)
                    inf_entries = []
                    for tit, val in re.findall('<b>(.*?)</b>: (.*?)<br>', info):
                        sh_head['info_'+tit] = val
                        inf_entries.append(val)
                    if inf_entries:
                        sh_head['info'] = inf_entries
                # Extract extra info
                m = re.search(r'<td colspan="2" class="cell-extra-info">((?:\s+.*?)+)</td>', body, re.MULTILINE)
                if m:
                    info = m.group(1)
                    inf_entries = []
                    for val in re.findall('<b>(.*?)</b><br>', info):
                        inf_entries.append(val)
                    if inf_entries:
                        sh_head['extra_info'] = inf_entries
                # Extract stats
                m = re.search(r'<td class="cell-stats">((?:\s+.*?)+)</td>', body, re.MULTILINE)
                if m:
                    stats = m.group(1)
                    stats_entries = []
                    for tit, val in re.findall(r'<b>(.*?)</b>:\s+(\d+).*?<br>', stats):
                        val = int(val)
                        sh_head['stats_'+tit] = val
                        stats_entries.append(val)
                    if stats_entries:
                        sh_head['stats'] = stats_entries
            elif cl == 'content-table':
                # Header
                m = re.search(r'<tr[^>]*>\s+((?:<th.*?>(?:.*)</th>\s+)+)</tr>', body, re.MULTILINE)
                assert m, 'Failed to get table header'
                h = []
                head = m.group(1)
                for col_name in re.findall(r'<th.*?>(.*)</th>', head):
                    h.append(col_name)
                headers.append(h)
                # Rows
                b = []
                for row_txt in re.findall(r'<tr[^>]*>\s+((?:<td.*?>(?:.*)</td>\s+)+)</tr>', body, re.MULTILINE):
                    r = []
                    for cell in re.findall(r'<td.*?>(.*?)</td>', row_txt, re.MULTILINE):
                        if '<div' in cell:
                            r.append(cell.split('>')[-1])
                        else:
                            r.append(cell)
                    b.append(r)
                rows.append(b)
        return rows, headers, sh_head

    def load_html_style(self, filename):
        file = self.expect_out_file(os.path.join(self.sub_dir, filename))
        with open(file) as f:
            html = f.read()
        m = re.search(r'<style>((?:\s+.*?)+)</style>', html, re.MULTILINE)
        assert m
        return m.group(1)

    def load_xml(self, filename):
        rows = []
        headers = None
        for child in ET.parse(self.expect_out_file(os.path.join(self.sub_dir, filename))).getroot():
            rows.append(list(child.attrib.values()))
            if not headers:
                headers = list(child.attrib.keys())
        return rows, headers

    def load_xlsx(self, filename, sheet=1):
        """ Assumes the components are in sheet1 """
        file = self.expect_out_file(os.path.join(self.sub_dir, filename))
        subprocess.call(['unzip', file, '-d', self.get_out_path('desc')])
        # Some XMLs are stored with 0600 preventing them to be read by next CI/CD stage
        subprocess.call(['chmod', '-R', 'og+r', self.get_out_path('desc')])
        # Read the table
        worksheet = self.get_out_path(os.path.join('desc', 'xl', 'worksheets', 'sheet'+str(sheet)+'.xml'))
        if not os.path.isfile(worksheet):
            return None, None, None
        rows = []
        root = ET.parse(worksheet).getroot()
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        rnum = 1
        rfirst = 1
        sh_head = []
        for r in root.iter(ns+'row'):
            rcur = int(r.attrib['r'])
            if rcur > rnum:
                sh_head = rows
                # Discard the sheet header
                rows = []
                rnum = rcur
                rfirst = rcur
            this_row = []
            for cell in r.iter(ns+'c'):
                if 't' in cell.attrib:
                    type = cell.attrib['t']
                else:
                    type = 'n'   # default: number
                value = cell.find(ns+'v')
                if value is not None:
                    if type == 'n':
                        # Numbers as integers
                        value = int(value.text)
                    else:
                        value = value.text
                    this_row.append(value)
            rows.append(this_row)
            rnum += 1
        # Links are "Relationship"s
        links = {}
        nr = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
        hlinks = root.find(ns+'hyperlinks')
        if hlinks:
            for r in hlinks.iter(ns+'hyperlink'):
                links[r.attrib['ref']] = r.attrib[nr+'id']
        # Read the strings
        strings = self.get_out_path(os.path.join('desc', 'xl', 'sharedStrings.xml'))
        strs = [t.text for t in ET.parse(strings).getroot().iter(ns+'t')]
        # Replace the indexes by the strings
        for r in rows:
            for i, val in enumerate(r):
                if isinstance(val, str):
                    r[i] = strs[int(val)]
        for r in sh_head:
            for i, val in enumerate(r):
                if isinstance(val, str):
                    r[i] = strs[int(val)]
        # Translate the links
        if links:
            # Read the relationships
            worksheet = self.get_out_path(os.path.join('desc', 'xl', 'worksheets', '_rels', 'sheet'+str(sheet)+'.xml.rels'))
            root = ET.parse(worksheet).getroot()
            rels = {}
            for r in root:
                rels[r.attrib['Id']] = r.attrib['Target']
            # Convert cells to HTTP links
            for k, v in links.items():
                # Adapt the coordinate
                rnum = int(k[1:])-rfirst
                cnum = ord(k[0])-ord('A')
                # Get the link
                url = rels[v]
                rows[rnum][cnum] = '<a href="{}">{}</a>'.format(url, rows[rnum][cnum])
        # Separate the headers
        headers = rows.pop(0)
        return rows, headers, sh_head

    def test_compress(self, fname, files):
        logging.debug('Checking compressed output: '+fname)
        if fname.endswith('.zip'):
            cmd = ['unzip', '-t', self.get_out_path(fname)]
        elif fname.endswith('.rar'):
            cmd = ['rar', 't', self.get_out_path(fname)]
        else:
            cmd = ['tar', 'tvf', self.get_out_path(fname)]
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        text = res.decode()
        if fname.endswith('.zip'):
            assert 'No errors detected' in text
        elif fname.endswith('.rar'):
            assert 'All OK' in text
        for f in files:
            assert f in text, f
            logging.debug('- `'+f+'` OK')

    def test_compress_d(self, fname, files):
        self.test_compress(fname, [os.path.join(self.sub_dir, f) for f in files])

    def read_mk_targets(self, mkfile):
        targets = {}
        with open(mkfile, 'rt') as f:
            for line in f.readlines():
                parts = line.split(':')
                if len(parts) == 2:
                    targets[parts[0].strip()] = parts[1].strip()
        return targets

    def home_local_link(self):
        """ Make sure that ./tests can be used as a replacement for HOME.
            Currently just links ~/.local """
        home = os.environ.get('HOME')
        if home is not None:
            local = os.path.join(home, '.local')
            fake_local = os.path.join('tests', '.local')
            if os.path.isdir(local) and not os.path.isdir(fake_local):
                os.symlink(local, fake_local)


class TestContextSCH(TestContext):

    def __init__(self, test_dir, board_name, yaml_name, sub_dir='', test_name=None):
        self.mode = MODE_SCH
        if test_name is None:
            test_name = sys._getframe(1).f_code.co_name
        super().__init__(test_dir, board_name, yaml_name, sub_dir, test_name=test_name)

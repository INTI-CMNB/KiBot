#!/usr/bin/python3
VERSION = "1.9.1"
DRY = False

from datetime import datetime
import re
import subprocess
import sys
if sys.stdout.isatty():
    CSI = '\033['
    RED = CSI+str(31)+'m'
    GREEN = CSI+str(32)+'m'
    YELLOW = CSI+str(33)+'m'
    YELLOW2 = CSI+str(93)+'m'
    RESET = CSI+str(39)+'m'
    BRIGHT = CSI+";1;4"+'m'
    NORMAL = CSI+'0'+'m'
else:
    RED = GREEN = YELLOW = YELLOW2 = RESET = BRIGHT = NORMAL = ''


def read_file(fname):
    with open(fname, 'rt') as f:
        return f.read()


def write_file(fname, txt):
    if DRY:
        return
    with open(fname, 'wt') as f:
        f.write(txt)


def replace_txt(pattern, repl, txt):
    new_txt = re.sub(pattern, repl, txt)
    return new_txt, new_txt != txt


def msg(txt):
    print(txt)


def warn(txt):
    print(YELLOW+txt+RESET)


def err(txt):
    print(RED+txt+RESET)
    exit(1)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


today = datetime.now().strftime('%Y-%m-%d')
# Ensure global version
txt = read_file('kibot/__init__.py')
txt, changed = replace_txt(r"__version__ = '(.*)'", f"__version__ = '{VERSION}'", txt)
if changed:
    warn(f"Updating __version__ to {VERSION}")
else:
    msg("Version ok")
write_file('kibot/__init__.py', txt)

# Ensure Debian version
ver_debian = VERSION
if re.search(r'-\d+$', ver_debian) is None:
    ver_debian += '-1'
txt = read_file('debian/changelog')
res = re.match(r'^kibot \(([\d\.-]+)\) (\w+);', txt)
if res is None:
    err('Wrong Debian changelog')
cur_version = res.group(1)
cur_status = res.group(2)
if cur_version != ver_debian:
    warn(f'Updating Debian version to {ver_debian}')
if cur_status == 'UNRELEASED':
    warn('Updating release status')
if cur_version != ver_debian or cur_status == 'UNRELEASED':
    if not DRY:
        msg('- Change status to stable')
        run(['dch', '-v', ver_debian])
else:
    msg('Debian changelog ok')
txt = read_file('debian/changelog')
res = re.match(r'^kibot \(([\d\.-]+)\) (\w+);', txt)
if res is None:
    err('Wrong Debian changelog')
cur_version = res.group(1)
cur_status = res.group(2)
if cur_version != ver_debian:
    err('Wrong Debian version found')
if cur_status == 'UNRELEASED':
    err('Wrong Debian status')

# Check the CHANGELOG.md
CHLOG = 'CHANGELOG.md'
txt = read_file(CHLOG)
res = re.search(r'## \[([\d\.-]+)\] - (.*)', txt)
if res is None:
    err(f'No releases in {CHLOG}')
cur_version = res.group(1)
cur_date = res.group(2).strip()
if cur_version != VERSION:
    warn(f'Updating {CHLOG} version to {VERSION}')
if cur_date != today:
    warn(f'Updating date to {today}')
txt, changed = replace_txt(r'## \['+cur_version+r'\] - (.*)', f'## [{VERSION}] - {today}', txt)
if changed:
    write_file(CHLOG, txt)
else:
    msg(f'{CHLOG} ok')

# Regenerate docs
msg('Regenerating docs ...')
if not DRY:
    run(['make', 'doc'])

# Debian package
# Esto va desde el master
# msg('Generating Debian package ...')
# if not DRY:
#     run(['make', 'deb'])
#     run(['make', 'deb_clean'])

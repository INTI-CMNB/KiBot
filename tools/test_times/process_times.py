"""
This script analayzes the times from `pytest --durations=0`
"""
import re
import math

file = '1067.dat'
MAX_W = 200
cut = 0.9

re_tm = re.compile(r'([\d\.]+)s call\s+(.*)')
histo = None
total_tm = 0
total_n = 0
tests = {}
with open(file, 'rt') as f:
    for ln in f:
        res = re_tm.search(ln)
        if res:
            tm = float(res.group(1))
            tst = res.group(2)
            tm_slot = math.floor(tm)
            if histo is None:
                histo = (tm_slot+1)*[0]
            histo[tm_slot] += 1
            total_tm += tm
            total_n += 1
            # print(f'{tm} {tst}')
            tests[tst] = tm

avg = total_tm/total_n
cut_n = math.ceil(cut*total_n)
acu = 0
cut_done = False
for slot, cantidad in enumerate(histo):
    if not cantidad:
        continue
    acu += cantidad
    if cantidad > MAX_W:
        bar = MAX_W*'*'+f'...* ({cantidad})'
    else:
        bar = cantidad*'*'
    print("%02d|%03d %s" % (slot+1, cantidad, bar))
    if not cut_done and acu >= cut_n:
        slot_cut = slot+1
        print('----')
        cut_done = True

print(f'Runs: {total_n}')
print(f'Total time: {round(total_tm)} s ({round(total_tm/60, 1)} m)')
print(f'Average: {round(avg, 1)} s')
print(f'Cut: {cut*100} % ({cut_n}): {slot_cut} s ({total_n-cut_n})')

with open('slowest.txt', 'wt') as f:
    for tst, tm in tests.items():
        if tm >= slot_cut:
            f.write(f'{tst} {tm}\n')

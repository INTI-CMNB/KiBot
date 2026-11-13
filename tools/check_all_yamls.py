#!/usr/bin/env python3
# Dependencies: importlib_resources pyyaml check-jsonschema
import json
import re
import yaml
import glob
from jsonschema import Draft7Validator

schema = json.load(open('docs/kibot_schema.json'))
v = Draft7Validator(schema)
failed = 0
for fname in glob.glob('tests/yaml_samples/*.kibot.yaml')+glob.glob('kibot/resources/config_templates/*.kibot.yaml'):
    print("\n\n"+fname)
    content = open(fname).read()
    if '# This file is invalid' in content:
        print("Skip")
        continue
    for n, text in enumerate(re.split(r"^\.\.\.$", content, flags=re.M)):
        try:
            doc = yaml.safe_load(text)
        except Exception:
            print('ERROR: Fails to load')
            doc = False
            failed += 1
        if not doc:
            continue
        print(f'--- document {n}: keys {list(doc)}')
        for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path)):
            print('/'.join(map(str, e.path)), 'ERROR ->', e.message[:150])
            failed += 1
            for sub in e.context or []:
                print('     ', '/'.join(map(str, sub.path)), '->', sub.message[:120])
if not failed:
    print("Ok!")
else:
    print(f"{failed} failed")

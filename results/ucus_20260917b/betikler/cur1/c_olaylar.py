from c_ort import *
import sys
v=yukle(sys.argv[1])
for tip in ("ARM","EV","MODE","ERR"):
    for d in v.get(tip,[]):
        print(f"{d['t']:9.3f} {tip} {({k:x for k,x in d.items() if k not in ('TimeUS','t')})}")

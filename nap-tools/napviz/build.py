#!/usr/bin/env python3
"""Build napviz.html: python3 build.py KERNEL_NAP_DIR [OUT]   (KERNEL_NAP_DIR = drivers/cpuidle/governors/nap)"""
import array, base64, re, struct, sys, zlib, os, json
kdir = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "napviz.html")
here = os.path.dirname(os.path.abspath(__file__))
dims = {k: int(v) for k, v in re.findall(r"#define (NAP_\w+) (\d+)", open(f"{kdir}/nap_dims.h").read())}
src = open(f"{kdir}/nap_weights.h").read()
def arr(name):
    m = re.search(r"static const float %s\[\d+\] = \{(.*?)\};" % name, src, re.S)
    return [float(x.rstrip("f")) for x in re.findall(r"[-+0-9.eE]+f", m.group(1))]
mu, sd, w1, b1, w2, b2 = (arr(n) for n in ("nap_mu", "nap_sd", "nap_w1", "nap_b1", "nap_w2", "nap_b2"))
kcrc = lambda b: zlib.crc32(b) ^ 0xFFFFFFFF
sig = kcrc(array.array("f", mu).tobytes() + array.array("f", sd).tobytes())
p = array.array("f", w1 + b1 + w2 + b2).tobytes()
blob = struct.pack("<8s12I", b"NAPWGT01", 1, dims["NAP_NT"], dims["NAP_NK"], dims["NAP_ND"], dims["NAP_NHID"], dims["NAP_NOUT"],
                   dims["NAP_GRID_LOG2_FIRST"], dims["NAP_TAIL_REP_NS"], len(p), kcrc(p), sig, 0) + p
data = dict(NT=dims["NAP_NT"], NK=dims["NAP_NK"], ND=dims["NAP_ND"], NHID=dims["NAP_NHID"], NOUT=dims["NAP_NOUT"], FIRST=dims["NAP_GRID_LOG2_FIRST"],
            TAIL_REP=dims["NAP_TAIL_REP_NS"], mu=mu, sd=sd, inputSig=sig)
tpl = open(f"{here}/template.html").read()
html = (tpl.replace("/*DATA*/", "const NAP_DATA = " + json.dumps(data) + ";\nconst NAP_DEFAULT_BLOB = \"" + base64.b64encode(blob).decode() + "\";")
           .replace("/*CORE*/", open(f"{here}/core.js").read()).replace("/*UI*/", open(f"{here}/ui.js").read()))
open(out, "w").write(html); print("wrote", out, len(html) // 1024, "KB")

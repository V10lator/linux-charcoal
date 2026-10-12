// node test_core.js KERNEL_NAP_DIR : forward pass of the viewer against the kernel's self-test vectors
const fs = require("fs"), path = require("path");
const kdir = process.argv[2];
const dims = {}; for (const m of fs.readFileSync(kdir + "/nap_dims.h", "utf8").matchAll(/#define (NAP_\w+) (\d+)/g)) dims[m[1]] = +m[2];
const wsrc = fs.readFileSync(kdir + "/nap_weights.h", "utf8");
const arr = (src, name) => { const m = src.match(new RegExp("static const float " + name + "\\[\\d+\\] = \\{([\\s\\S]*?)\\};")); return [...m[1].matchAll(/[-+0-9.eE]+f/g)].map((x) => parseFloat(x[0])); };
const mu = arr(wsrc, "nap_mu"), sd = arr(wsrc, "nap_sd");
global.NAP_DATA = { NT: dims.NAP_NT, NK: dims.NAP_NK, ND: dims.NAP_ND, NHID: dims.NAP_NHID, NOUT: dims.NAP_NOUT, FIRST: dims.NAP_GRID_LOG2_FIRST, TAIL_REP: dims.NAP_TAIL_REP_NS, mu, sd, inputSig: 0 };
const C = require("./core.js");
const model = { w1: Float32Array.from(arr(wsrc, "nap_w1")), b1: Float32Array.from(arr(wsrc, "nap_b1")), w2: Float32Array.from(arr(wsrc, "nap_w2")), b2: Float32Array.from(arr(wsrc, "nap_b2")) };
const ssrc = fs.readFileSync(kdir + "/nap_selftest.h", "utf8"), inp = arr(ssrc, "nap_st_in"), out = arr(ssrc, "nap_st_out");
let worst = 0; const nv = inp.length / 16;
for (let v = 0; v < nv; v++) { const r = C.forward(model, inp.slice(v * 16, v * 16 + 16)); for (let o = 0; o < 16; o++) worst = Math.max(worst, Math.abs(r.S[o] - out[v * 16 + o])); }
console.log(`forward: ${nv} vectors, worst |S_js - S_kernel_ref| = ${worst.toExponential(2)}`);
if (worst > 1e-4) { console.log("FAIL"); process.exit(1); }
// decision sanity: long timer -> deep state, very short -> POLL
const states = [{ name: "POLL", target: 0, exit: 0, pow: 1 }, { name: "C1", target: 2000, exit: 1000, pow: 0.5 }, { name: "C2", target: 36000, exit: 18000, pow: 0.2 }, { name: "C3", target: 700000, exit: 350000, pow: 0.05 }];
for (const sl of [10, 14, 17, 20, 24, 27]) {
  const x = C.defaultFeatures(); x[0] = sl; x[1] = sl - Math.log2(1e6);
  const r = C.forward(model, x), d = C.decide(r.S, states, { tick: 1e6, sleep: Math.pow(2, sl), cs: 3000, cw: 5000, lam: 1, tickNs: 1e6 });
  console.log(`sleep 2^${sl} ns: best = ${states[d.best.k].name}${d.best.stop ? " + stop tick" : ""}; E[idle] = ${(C.expectedIdle(r.S) / 1e3).toFixed(1)} us`);
}
console.log("OK");

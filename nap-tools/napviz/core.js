/* napviz core: nap weight blob parsing, the network's forward pass and the governor's decision.
 * Mirrors drivers/cpuidle/governors/nap (nap_encode, the nn forward, nap_fpu_select).  No DOM here. */
"use strict";
const NAPC = (() => {
  const D = NAP_DATA;                       // {NT,NK,ND,NHID,NOUT,FIRST,TAIL_REP,mu[],sd[], inputSig}
  const NROW = D.NT * D.NK + D.ND, NNZ = 2 * D.NT + D.ND, NB = D.NOUT + 1;
  const TI = [0, 7, 8, 9, 10, 11, 12, 5], DI = [1, 2, 3, 4, 6, 13, 14, 15];
  const FEATURES = [
    "time to next timer (log2 ns)", "tick ratio (log2 sleep/tick)", "busy CPUs (log1p)", "wakes in last 50us (log1p)", "wakes in last 1ms (log1p)",
    "last busy period (log2 ns)", "irqs while busy (log1p)",
    "idle history h1 (log2 ns)", "h2", "h3", "h4", "h5", "h6",
    "last wake: device irq (log1p)", "last wake: local timer (log1p)", "last wake: call IPI (log1p)"];

  // ---- crc32 as the kernel's crc32_le(~0, data): zlib crc32 without the final inversion
  const T32 = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; T32[n] = c >>> 0; }
  function kcrc(bytes, start = 0xFFFFFFFF) { let c = start >>> 0; for (let i = 0; i < bytes.length; i++) c = T32[(c ^ bytes[i]) & 255] ^ (c >>> 8); return c >>> 0; }

  const HDR = 56;
  function parseBlob(buf) {                 // buf: ArrayBuffer of one blob
    const dv = new DataView(buf), u8 = new Uint8Array(buf);
    if (buf.byteLength < HDR) throw new Error("file too short");
    const magic = String.fromCharCode(...u8.slice(0, 8));
    if (magic !== "NAPWGT01") throw new Error("not a nap weight file (magic=" + magic + ")");
    const f = []; for (let i = 0; i < 12; i++) f.push(dv.getUint32(8 + 4 * i, true));
    const [fmt, nt, nk, nd, nhid, nout, first, tail, pbytes, crc, sig] = f;
    if (fmt !== 1 || nt !== D.NT || nk !== D.NK || nd !== D.ND || nhid !== D.NHID || nout !== D.NOUT || first !== D.FIRST)
      throw new Error("network shape differs from this viewer");
    if (buf.byteLength !== HDR + pbytes) throw new Error("size does not match the header");
    const crcOk = kcrc(u8.subarray(HDR)) === crc;
    const n1 = NROW * D.NHID, nw2 = D.NOUT * D.NHID;
    const fl = new Float32Array(buf.slice(HDR));
    return { w1: fl.subarray(0, n1), b1: fl.subarray(n1, n1 + D.NHID), w2: fl.subarray(n1 + D.NHID, n1 + D.NHID + nw2),
             b2: fl.subarray(n1 + D.NHID + nw2), crcOk, sigOk: sig === D.inputSig, tailRep: tail };
  }
  function parseState(buf) {                // NAPSTAT1 container -> [{cpu, model}]
    const dv = new DataView(buf), u8 = new Uint8Array(buf);
    if (String.fromCharCode(...u8.slice(0, 8)) !== "NAPSTAT1") return null;
    const n = dv.getUint32(8, true); let pos = 8 + 4 + 32; const out = [];
    for (let i = 0; i < n; i++) {
      const cpu = dv.getUint32(pos, true), len = dv.getUint32(pos + 4, true); pos += 8;
      out.push({ cpu, model: parseBlob(buf.slice(pos, pos + len)) }); pos += len;
    }
    return out;
  }

  // ---- features -> sparse input, like nap_encode()
  function encode(x) {
    const idx = [], coef = [], top = D.NK - 1 - 1e-4;
    for (let t = 0; t < D.NT; t++) {
      let u = x[TI[t]] - D.FIRST; u = u < 0 ? 0 : (u > top ? top : u); const k = Math.floor(u);
      idx.push(t * D.NK + k); coef.push(1 - (u - k)); idx.push(t * D.NK + k + 1); coef.push(u - k);
    }
    for (let i = 0; i < D.ND; i++) { idx.push(D.NT * D.NK + i); coef.push((x[DI[i]] - D.mu[i]) / D.sd[i]); }
    return { idx, coef };
  }
  const sigmoid = (v) => 1 / (1 + Math.exp(-v));
  function forward(m, x) {
    const { idx, coef } = encode(x), H = D.NHID, hid = new Float32Array(H);
    for (let j = 0; j < H; j++) hid[j] = m.b1[j];
    for (let i = 0; i < NNZ; i++) { const r = idx[i] * H, c = coef[i]; for (let j = 0; j < H; j++) hid[j] += c * m.w1[r + j]; }
    for (let j = 0; j < H; j++) if (hid[j] < 0) hid[j] = 0;
    const logit = new Float32Array(D.NOUT), S = new Float32Array(D.NOUT);
    for (let o = 0; o < D.NOUT; o++) { let a = m.b2[o]; const r = o * H; for (let j = 0; j < H; j++) a += m.w2[r + j] * hid[j]; logit[o] = a; S[o] = sigmoid(a); }
    return { hid, logit, S, idx, coef };
  }

  // ---- decision, like nap_fpu_select()
  function binTimes() {
    const Tb = new Float64Array(NB); Tb[0] = Math.pow(2, D.FIRST - 1);
    for (let b = 1; b < D.NOUT; b++) Tb[b] = 1.4427 * Math.pow(2, D.FIRST - 1 + b);
    Tb[D.NOUT] = D.TAIL_REP; return Tb;
  }
  function binProbs(S) {                    // monotone survival -> bin probabilities
    const Sm = new Float64Array(D.NOUT); Sm[0] = S[0];
    for (let i = 1; i < D.NOUT; i++) Sm[i] = Math.min(S[i], Sm[i - 1]);
    const p = new Float64Array(NB); p[0] = 1 - Sm[0];
    for (let b = 1; b < D.NOUT; b++) p[b] = Sm[b - 1] - Sm[b];
    p[D.NOUT] = Sm[D.NOUT - 1]; return p;
  }
  function ideal(tgt, T) { for (let j = tgt.length - 1; j > 0; j--) if (tgt[j] <= T) return j; return 0; }
  /* states: [{name, target, exit, pow}] ; opt: {tick, sleep, cs, cw, lam, tickNs(=TICK_NSEC)} */
  function decide(S, states, opt) {
    const ns = states.length, tgt = states.map((s) => s.target), ex = states.map((s) => s.exit), pw = states.map((s) => s.pow);
    const e0 = [0]; for (let k = 1; k < ns; k++) e0.push(e0[k - 1] + (pw[k - 1] - pw[k]) * tgt[k]);
    const p = binProbs(S), Tb = binTimes(), tick = Math.max(opt.tick, 1);
    const nf = [], rem = [], kb = [], kc = [];
    for (let b = 0; b < NB; b++) {
      nf.push(Math.trunc(Tb[b] / tick)); rem.push(Tb[b] - nf[b] * tick);
      kb.push(ideal(tgt, Tb[b])); kc.push(ideal(tgt, rem[b] > 0 ? rem[b] : tick));
    }
    const cand = []; let best = -Infinity, bi = -1;
    for (let k = 0; k < ns; k++) {
      const keepE = e0[k] + pw[k] * tick + opt.cw;
      for (let st = 0; st < 2; st++) {
        if (k === 0 && st) continue;
        const entry = { k, stop: !!st, E: 0, L: 0, v: 0, allowed: true };
        if (st && opt.sleep < opt.tickNs) { entry.allowed = false; cand.push(entry); continue; }
        for (let b = 0; b < NB; b++) {
          if (p[b] < 1e-4) continue;
          const T = Tb[b]; let e, o;
          if (k === 0) { e = pw[0] * T; o = 0; }
          else if (st) { e = e0[k] + pw[k] * T + opt.cs; o = Math.max(0, ex[k] - ex[kb[b]]); }
          else { e = nf[b] * keepE; o = Math.max(0, ex[k] - ex[kc[b]]); if (rem[b] > 0) e += e0[k] + pw[k] * rem[b] + opt.cw; }
          entry.E += p[b] * e; entry.L += p[b] * o;
        }
        entry.v = -entry.E - opt.lam * entry.L;
        if (entry.v > best) { best = entry.v; bi = cand.length; }
        cand.push(entry);
      }
    }
    return { cand, best: cand[bi], p, Tb };
  }
  function expectedIdle(S) { const p = binProbs(S), Tb = binTimes(); let a = 0; for (let b = 0; b < NB; b++) a += p[b] * Tb[b]; return a; }

  /* default feature vector for a quiet system with a 1 ms tick */
  function defaultFeatures() {
    const sleep = 20, tickNs = 1e6;       // log2(1e6)~19.93
    const x = new Array(16).fill(0);
    x[0] = sleep; x[1] = sleep - Math.log2(tickNs); x[2] = Math.log1p(1); x[3] = Math.log1p(0); x[4] = Math.log1p(2);
    x[5] = 16; x[6] = Math.log1p(2); for (let i = 7; i <= 12; i++) x[i] = 17; x[13] = Math.log1p(1); x[14] = Math.log1p(1); x[15] = Math.log1p(0);
    return x;
  }
  return { D, NROW, NNZ, NB, TI, DI, FEATURES, parseBlob, parseState, encode, forward, decide, binProbs, binTimes, expectedIdle, defaultFeatures, kcrc, ideal };
})();
if (typeof module !== "undefined") module.exports = NAPC;

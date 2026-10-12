"use strict";
/* ---------- helpers ---------- */
const $ = (s, r = document) => r.querySelector(s);
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) { if (k === "on") for (const [ev, fn] of Object.entries(v)) e.addEventListener(ev, fn); else if (k === "html") e.innerHTML = v; else e.setAttribute(k, v); }
  for (const c of kids.flat()) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
}
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const dark = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
function fmtT(ns) { if (ns < 1e3) return ns.toFixed(ns < 10 ? 1 : 0) + " ns"; if (ns < 1e6) return (ns / 1e3).toFixed(ns < 1e4 ? 1 : 0) + " µs"; if (ns < 1e9) return (ns / 1e6).toFixed(ns < 1e7 ? 2 : 1) + " ms"; return (ns / 1e9).toFixed(2) + " s"; }
function canvasSetup(cv, hpx) { const dpr = window.devicePixelRatio || 1, w = cv.clientWidth || 600; cv.width = w * dpr; cv.height = hpx * dpr; cv.style.height = hpx + "px"; const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.font = "12px system-ui,sans-serif"; return { g, w, h: hpx }; }
const PAL = ["#8c96a3", "#4c8bf5", "#2fb36d", "#e8912d", "#c0504d", "#8e5bd1", "#17a2b8", "#d6336c", "#7f8c2e", "#5d6d7e"];
function shade(hex, f) { const n = parseInt(hex.slice(1), 16); return "rgb(" + [n >> 16, (n >> 8) & 255, n & 255].map((v) => Math.max(0, Math.min(255, Math.round(v * f)))).join(",") + ")"; }
const timeTicks = (lo, hi, step) => { const t = []; for (let v = lo; v <= hi; v += step) t.push({ v, label: fmtT(Math.pow(2, v)).replace(" ", "") }); return t; };

/* ---------- charts (canvas) ---------- */
function lineChart(cv, o) {
  const { g, w, h: H } = canvasSetup(cv, o.height || 220); const L = 46, R = 10, T = 8, B = 28, pw = w - L - R, ph = H - T - B;
  const ink = css("--ink"), sub = css("--sub"), line = css("--line");
  const xs = o.xmin ?? Math.min(...o.xs), xe = o.xmax ?? Math.max(...o.xs); const all = o.series.flatMap((s) => Array.from(s.ys));
  const y0 = o.ymin ?? Math.min(...all), y1 = o.ymax ?? Math.max(...all); const yy = y1 === y0 ? 1 : y1 - y0;
  const X = (v) => L + ((v - xs) / (xe - xs)) * pw, Y = (v) => T + ph - ((v - y0) / yy) * ph;
  g.strokeStyle = line; g.fillStyle = sub; g.lineWidth = 1; g.textAlign = "right";
  for (let i = 0; i <= 4; i++) { const v = y0 + (yy * i) / 4, y = Y(v); g.beginPath(); g.moveTo(L, y); g.lineTo(L + pw, y); g.stroke(); g.fillText((o.yfmt || ((q) => q.toFixed(2)))(v), L - 5, y + 4); }
  g.textAlign = "center"; for (const t of o.xticks || []) { const x = X(t.v); g.beginPath(); g.moveTo(x, T + ph); g.lineTo(x, T + ph + 4); g.stroke(); g.fillText(t.label, x, T + ph + 16); }
  for (const s of o.series) { g.strokeStyle = s.color; g.lineWidth = s.w || 2; g.setLineDash(s.dash || []); g.beginPath(); o.xs.forEach((x, i) => (i ? g.lineTo(X(x), Y(s.ys[i])) : g.moveTo(X(x), Y(s.ys[i])))); g.stroke(); g.setLineDash([]);
    if (s.dots) for (let i = 0; i < o.xs.length; i++) { g.fillStyle = s.color; g.beginPath(); g.arc(X(o.xs[i]), Y(s.ys[i]), 2.5, 0, 7); g.fill(); } }
  if (o.marker != null) { g.strokeStyle = ink; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(X(o.marker), T); g.lineTo(X(o.marker), T + ph); g.stroke(); g.setLineDash([]); }
  let lx = L + 8; g.textAlign = "left"; for (const s of o.series) if (s.label) { g.fillStyle = s.color; g.fillRect(lx, T + 4, 10, 10); g.fillStyle = ink; g.fillText(s.label, lx + 14, T + 13); lx += 22 + g.measureText(s.label).width; }
}
function barChart(cv, o) {
  const { g, w, h: H } = canvasSetup(cv, o.height || 190); const L = 8, B = o.rot ? 74 : 26, T = 6, n = o.vals.length, bw = (w - L * 2) / n; const mx = Math.max(...o.vals, 1e-12);
  o.vals.forEach((v, i) => { const bh = (v / mx) * (H - T - B), x = L + i * bw; g.fillStyle = (o.colors && o.colors[i]) || css("--acc"); g.globalAlpha = 0.85; g.fillRect(x + 1, H - B - bh, Math.max(1, bw - 2), bh); g.globalAlpha = 1;
    if (o.labels && (n <= 24 || i % Math.ceil(n / 24) === 0)) { g.save(); g.fillStyle = css("--sub"); g.translate(x + bw / 2, H - B + 12); if (o.rot) g.rotate(-0.7); g.textAlign = o.rot ? "right" : "center"; g.fillText(o.labels[i], 0, 0); g.restore(); } });
  if (o.vfmt) { g.fillStyle = css("--sub"); g.textAlign = "right"; g.fillText("max " + o.vfmt(mx), w - 6, 14); }
}
function histChart(cv, series, o = {}) {
  const { g, w, h: H } = canvasSetup(cv, o.height || 160); const L = 8, R = 8, T = 8, B = 22, nb = 41;
  let m = 0; for (const s of series) for (const v of s.vals) m = Math.max(m, Math.abs(v)); const lim = m || 1;
  const hs = series.map((s) => { const c = new Float64Array(nb); for (const v of s.vals) c[Math.min(nb - 1, Math.max(0, Math.floor(((v + lim) / (2 * lim)) * nb)))]++; return c; });
  const mx = Math.max(...hs.map((c) => Math.max(...c))), bw = (w - L - R) / nb;
  g.strokeStyle = css("--line"); g.beginPath(); g.moveTo(L, H - B); g.lineTo(w - R, H - B); g.stroke();
  hs.forEach((c, si) => { g.fillStyle = series[si].color; g.globalAlpha = hs.length > 1 ? 0.55 : 0.85; c.forEach((v, i) => { const bh = Math.log1p(v) / Math.log1p(mx) * (H - T - B); g.fillRect(L + i * bw, H - B - bh, Math.max(1, bw - 1), bh); }); g.globalAlpha = 1; });
  g.fillStyle = css("--sub"); g.textAlign = "center"; for (const f of [-1, -0.5, 0, 0.5, 1]) g.fillText((f * lim).toFixed(lim < 1 ? 2 : 1), L + 8 + ((f + 1) / 2) * (w - L - R - 16), H - 7);
  g.textAlign = "left"; g.fillText("count (log scale), max " + mx, L + 4, T + 8);
}
function divColor(t) { t = Math.max(-1, Math.min(1, t)); const a = Math.abs(t), c = t < 0 ? [37, 99, 235] : [220, 70, 40], bg = dark() ? 34 : 248; return "rgb(" + c.map((k) => Math.round(bg + (k - bg) * a)).join(",") + ")"; }
function heatChart(cv, M, o) {
  const rows = M.length, cols = M[0].length, Lb = 62; const { g, w, h: H } = canvasSetup(cv, o.height || 26 + rows * 12); const cw = (w - Lb - 4) / cols, ch = (H - 24) / rows;
  const vmax = o.vmax || Math.max(...M.flatMap((r) => Array.from(r).map(Math.abs)), 1e-9);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) { g.fillStyle = divColor(M[r][c] / vmax); g.fillRect(Lb + c * cw, 24 + r * ch, Math.ceil(cw), Math.ceil(ch)); }
  g.fillStyle = css("--sub"); g.textAlign = "right"; (o.rowLabels || []).forEach((l, r) => { if (rows <= 24 || r % 2 === 0) g.fillText(l, Lb - 4, 24 + r * ch + ch * 0.8); });
  g.textAlign = "left"; g.fillText(o.title || "", Lb, 12);
  if (o.hl != null) { g.strokeStyle = css("--ink"); g.lineWidth = 1.5; g.strokeRect(Lb + o.hl * cw, 24, Math.max(2, cw), rows * ch); g.lineWidth = 1; }
  cv.onclick = o.onClick ? (e) => { const r = cv.getBoundingClientRect(); const c = Math.floor((e.clientX - r.left - Lb) / cw); if (c >= 0 && c < cols) o.onClick(c); } : null;
}
function catMap(cv, grid, o) {       // grid[r][c] = category index or -1
  const rows = grid.length, cols = grid[0].length, Lb = 54; const { g, w, h: H } = canvasSetup(cv, o.height || 300); const cw = (w - Lb - 6) / cols, ch = (H - 34) / rows;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) { const k = grid[r][c]; g.fillStyle = k < 0 ? css("--cell") : o.colors[k]; g.fillRect(Lb + c * cw, 4 + (rows - 1 - r) * ch, Math.ceil(cw), Math.ceil(ch)); }
  g.fillStyle = css("--sub"); g.textAlign = "right"; o.rowTicks.forEach((t) => g.fillText(t.label, Lb - 4, 4 + (rows - 1 - t.i) * ch + ch * 0.8)); g.textAlign = "center"; o.colTicks.forEach((t) => g.fillText(t.label, Lb + (t.i + 0.5) * cw, H - 18));
  g.textAlign = "left"; g.fillText(o.xlabel, Lb, H - 4);
  if (o.mark) { g.strokeStyle = css("--ink"); g.lineWidth = 2; g.beginPath(); g.arc(Lb + (o.mark.c + 0.5) * cw, 4 + (rows - 1 - o.mark.r) * ch + ch / 2, 5, 0, 7); g.stroke(); g.lineWidth = 1; }
}

/* ---------- state ---------- */
const D = NAPC.D;
const S = { models: { A: null, B: null }, names: { A: "built-in default model", B: "" }, active: "A", tab: "overview", embed: { t: 0, unit: 0, out: 11, feat: 0 },
  tick: 1e6, tickKernel: 1e6, lam: 1, cs: 3000, cw: 5000,
  states: [{ name: "POLL", target: 0, exit: 0, pow: 1 }, { name: "C1", target: 2, exit: 1, pow: 0.5 }, { name: "C2", target: 36, exit: 18, pow: 0.2 }, { name: "C3", target: 700, exit: 350, pow: 0.05 }] };
const FS = [{ x: 0, label: "Time to next timer", kind: "time", min: 9, max: 30, def: 20 }, null,
  { x: 2, label: "Busy CPUs", kind: "count", min: 0, max: 64, def: 1 }, { x: 3, label: "Wakes in last 50 µs", kind: "count", min: 0, max: 64, def: 0 },
  { x: 4, label: "Wakes in last 1 ms", kind: "count", min: 0, max: 200, def: 2 }, { x: 5, label: "Last busy period", kind: "time", min: 0, max: 30, def: 16 },
  { x: 6, label: "IRQs while busy", kind: "count", min: 0, max: 200, def: 2 },
  ...[1, 2, 3, 4, 5, 6].map((i) => ({ x: 6 + i, label: "Idle history h" + i + (i === 1 ? " (latest)" : ""), kind: "time", min: 0, max: 30, def: 17 })),
  { x: 13, label: "Last wake: device IRQ", kind: "count", min: 0, max: 64, def: 1 }, { x: 14, label: "Last wake: local timer", kind: "count", min: 0, max: 64, def: 1 },
  { x: 15, label: "Last wake: call IPI", kind: "count", min: 0, max: 64, def: 0 }];
S.v = new Array(16).fill(0); for (const f of FS) if (f) S.v[f.x] = f.def;
function X16(v) { v = v || S.v; const x = new Array(16).fill(0); for (const f of FS) if (f) x[f.x] = f.kind === "count" ? Math.log1p(v[f.x]) : v[f.x]; x[1] = v[0] - Math.log2(S.tick); return x; }
const mdl = (k) => S.models[k || S.active];
const stStates = () => S.states.map((s) => ({ name: s.name, target: s.target * 1e3, exit: s.exit * 1e3, pow: s.pow }));
const dopt = (sleep) => ({ tick: S.tick, sleep: sleep ?? Math.pow(2, S.v[0]), cs: S.cs, cw: S.cw, lam: S.lam, tickNs: S.tickKernel });
const gridT = (o) => Math.pow(2, D.FIRST + o);
const statLabel = (st, c) => st[c.k].name + (c.stop ? " + stop tick" : "");

/* ---------- common UI ---------- */
function featureSliders(onChange) {
  const box = h("div", {});
  for (const f of FS) {
    if (!f) { box.append(h("div", { class: "row" }, h("label", {}, "Tick ratio (derived)"), h("div", {}, h("input", { type: "number", value: S.tick, step: 100000, on: { change: (e) => { S.tick = +e.target.value || 1e6; onChange(); } } }), " tick period, ns"), h("output", { id: "o-tr" }, ""))); continue; }
    const out = h("output", {}), inp = h("input", { type: "range", min: f.min, max: f.max, step: f.kind === "time" ? 0.25 : 1, value: S.v[f.x] });
    const show = () => { out.textContent = f.kind === "time" ? (S.v[f.x] <= 0 ? "none" : fmtT(Math.pow(2, S.v[f.x]))) : String(S.v[f.x]); };
    inp.addEventListener("input", () => { S.v[f.x] = +inp.value; show(); const o = $("#o-tr"); if (o) o.textContent = (S.v[0] - Math.log2(S.tick)).toFixed(2); onChange(); });
    show(); box.append(h("div", { class: "row" }, h("label", {}, f.label), inp, out));
  }
  setTimeout(() => { const o = $("#o-tr"); if (o) o.textContent = (S.v[0] - Math.log2(S.tick)).toFixed(2) + " (log2)"; });
  return box;
}
const PRESETS = [
  ["Quiet, timer in 20 ms", { 0: 24.25, 5: 12, 7: 24, 8: 24, 9: 24, 10: 24, 11: 24, 12: 24, 2: 0, 3: 0, 4: 0, 6: 1 }],
  ["Periodic 1 ms timer", { 0: 19.9, 5: 14, 7: 19.9, 8: 19.9, 9: 19.9, 10: 19.9, 11: 19.9, 12: 19.9, 2: 1, 3: 0, 4: 1, 6: 2 }],
  ["Busy, short idles", { 0: 13, 5: 17, 7: 11, 8: 12, 9: 11, 10: 12, 11: 11, 12: 12, 2: 6, 3: 10, 4: 40, 6: 40 }],
  ["Just woke by IPI", { 0: 20, 5: 15, 7: 10, 8: 10, 9: 11, 10: 10, 11: 10, 12: 11, 2: 3, 3: 4, 4: 12, 6: 8, 13: 0, 14: 0, 15: 3 }],
];
function presetPills(onChange) { return h("div", {}, PRESETS.map(([n, p]) => h("span", { class: "pill", on: { click: () => { for (const [k, v] of Object.entries(p)) S.v[+k] = v; S.tick = 1e6; render(true); } } }, n))); }
function canvasCard(title, note, id, extra) { return h("div", { class: "card" }, h("h3", {}, title), note ? h("p", { class: "note" }, note) : null, h("canvas", { id }), extra || null); }

/* ---------- tabs ---------- */
const TABS = [["overview", "Overview"], ["embed", "Embeddings & sensitivity"], ["predict", "Predict"], ["decide", "Decision"], ["compare", "Compare"]];
function groupVals(m) { return [["Time-feature tables (8×16 knots × hidden)", m.w1.subarray(0, D.NT * D.NK * D.NHID)], ["Dense-feature rows (8 × hidden)", m.w1.subarray(D.NT * D.NK * D.NHID)], ["Hidden bias b1", m.b1], ["Output weights w2 (16 × hidden)", m.w2], ["Output bias b2", m.b2]]; }
const stats = (a) => { let mx = 0, s = 0, s2 = 0; for (const v of a) { mx = Math.max(mx, Math.abs(v)); s += Math.abs(v); s2 += v * v; } return { n: a.length, max: mx, mean: s / a.length, rms: Math.sqrt(s2 / a.length) }; };
function unitNorms(m) { const n = new Float64Array(D.NHID); for (let j = 0; j < D.NHID; j++) { let a = 0; for (let o = 0; o < D.NOUT; o++) a += m.w2[o * D.NHID + j] ** 2; n[j] = Math.sqrt(a); } return n; }

function renderOverview(root) {
  const m = mdl(), o = mdl(S.active === "A" ? "B" : "A"); root.replaceChildren();
  const info = h("div", { class: "card" }, h("h3", {}, "Network"), h("p", { class: "note" }, `16 features → ${D.NT} time features embedded piecewise-linearly on ${D.NK} knots (one octave apart, 2^${D.FIRST} … 2^${D.FIRST + D.NK - 1} ns) + ${D.ND} dense features → ${D.NHID} hidden units (ReLU) → ${D.NOUT} outputs: P(idle ≥ 2^(${D.FIRST}+g) ns). ${NAPC.NROW * D.NHID + D.NHID + D.NOUT * D.NHID + D.NOUT} parameters.`),
    h("p", {}, "Model ", h("b", {}, S.names[S.active]), ": checksum ", m.crcOk ? h("span", { class: "ok" }, "ok") : h("span", { class: "warn" }, "BAD"), ", input scaling ", m.sigOk ? h("span", { class: "ok" }, "matches this viewer") : h("span", { class: "warn" }, "DIFFERS (predictions may be off)"), "."));
  const grid = h("div", { class: "grid" }, info);
  const gv = groupVals(m), go = o ? groupVals(o) : null;
  gv.forEach(([name, vals], i) => {
    const st = stats(vals), id = "hist" + i;
    const series = [{ vals, color: css("--acc") }]; if (go) series.push({ vals: go[i][1], color: css("--acc2") });
    grid.append(canvasCard(name, `${st.n} values · mean |w| ${st.mean.toFixed(3)} · rms ${st.rms.toFixed(3)} · max |w| ${st.max.toFixed(2)}` + (go ? ` · blue = ${S.active}, orange = ${S.active === "A" ? "B" : "A"}` : ""), id));
    setTimeout(() => histChart($("#" + id), series), 0);
  });
  const un = unitNorms(m), order = Array.from(un.keys()).sort((a, b) => un[b] - un[a]); const mx = un[order[0]];
  grid.append(canvasCard("Hidden units by influence on the output", `Norm of each unit's outgoing weights, sorted. ${order.filter((j) => un[j] < 0.05 * mx).length} of ${D.NHID} units are below 5% of the strongest (nearly unused).`, "unitbars"));
  setTimeout(() => barChart($("#unitbars"), { labels: order.map(String), vals: order.map((j) => un[j]), vfmt: (v) => v.toFixed(2) }), 0);
  root.append(grid);
}

function renderEmbed(root) {
  const m = mdl(); root.replaceChildren(); const E = S.embed; const un = unitNorms(m), order = Array.from(un.keys()).sort((a, b) => un[b] - un[a]);
  const tsel = h("select", { on: { change: (e) => { E.t = +e.target.value; render(); } } }, NAPC.TI.map((xi, t) => h("option", { value: t, ...(t === E.t ? { selected: "" } : {}) }, NAPC.FEATURES[xi].replace(/ \(log2 ns\)/, ""))));
  const usel = h("input", { type: "number", min: 0, max: D.NHID - 1, value: E.unit, on: { change: (e) => { E.unit = Math.max(0, Math.min(D.NHID - 1, +e.target.value)); render(); } } });
  const osel = h("select", { on: { change: (e) => { E.out = +e.target.value; render(); } } }, Array.from({ length: D.NOUT }, (_, o) => h("option", { value: o, ...(o === E.out ? { selected: "" } : {}) }, `P(idle ≥ ${fmtT(gridT(o))})`)));
  const fsel = h("select", { on: { change: (e) => { E.feat = +e.target.value; render(); } } }, FS.map((f, i) => f ? h("option", { value: i, ...(i === E.feat ? { selected: "" } : {}) }, f.label) : null));
  root.append(h("div", { class: "card" }, h("p", { class: "note" }, "Time feature: ", tsel, "  Hidden unit (click a column or type): ", usel, "  Output: ", osel)));
  const grid = h("div", { class: "grid" });
  grid.append(canvasCard("Embedding table of the selected time feature", "Rows = 16 knots (the feature's value, 2^9 … 2^24 ns), columns = hidden units sorted by influence. Red = pushes the unit up, blue = down.", "hm"));
  grid.append(canvasCard("Selected unit's response to this feature", "The unit's first-layer weight at each knot (the piecewise-linear curve the unit applies to this feature).", "uc"));
  grid.append(canvasCard("Sensitivity: one feature swept, the rest as set in the Predict tab", "Output probability and how strongly each feature moves the selected output at the current operating point.", "sens", h("canvas", { id: "imp", style: "margin-top:8px" })));
  grid.firstChild.append(h("div", { class: "note", style: "margin-top:6px" }, "Sweep feature: ", fsel));
  root.append(grid);
  const rowsM = Array.from({ length: D.NK }, (_, k) => order.map((j) => m.w1[(E.t * D.NK + k) * D.NHID + j]));
  setTimeout(() => {
    heatChart($("#hm"), rowsM, { rowLabels: Array.from({ length: D.NK }, (_, k) => fmtT(Math.pow(2, D.FIRST + k)).replace(" ", "")), title: NAPC.FEATURES[NAPC.TI[E.t]], height: 26 + D.NK * 14, hl: order.indexOf(E.unit), onClick: (c) => { E.unit = order[c]; render(); } });
    const wv = Array.from({ length: D.NK }, (_, k) => m.w1[(E.t * D.NK + k) * D.NHID + E.unit]);
    lineChart($("#uc"), { xs: Array.from({ length: D.NK }, (_, k) => D.FIRST + k), series: [{ ys: wv, color: css("--acc"), dots: true, label: `unit ${E.unit}, outgoing weight to this output: ${m.w2[E.out * D.NHID + E.unit].toFixed(2)}` }], xticks: timeTicks(9, 24, 3), yfmt: (v) => v.toFixed(2), height: 200 });
    // sensitivity sweep
    const f = FS[E.feat], xs = [], ys = [], lg = []; const base = S.v.slice();
    const steps = f.kind === "time" ? 120 : Math.min(f.max, 64);
    for (let i = 0; i <= steps; i++) { const val = f.min + ((f.max - f.min) * i) / steps; const v = base.slice(); v[f.x] = f.kind === "count" ? Math.round(val) : val; const r = NAPC.forward(m, X16(v)); xs.push(val); ys.push(r.S[E.out]); }
    lineChart($("#sens"), { xs, series: [{ ys, color: css("--acc"), label: `P(idle ≥ ${fmtT(gridT(E.out))})` }], xmin: f.min, xmax: f.max, ymin: 0, ymax: 1, marker: base[f.x], xticks: f.kind === "time" ? timeTicks(Math.max(f.min, 9), f.max, 3) : Array.from({ length: 5 }, (_, i) => ({ v: f.min + ((f.max - f.min) * i) / 4, label: String(Math.round(f.min + ((f.max - f.min) * i) / 4)) })), height: 200 });
    const imp = FS.map((ff, i) => { if (!ff) return 0; let lo = 1, hi = 0; for (let s = 0; s <= 24; s++) { const val = ff.min + ((ff.max - ff.min) * s) / 24; const v = base.slice(); v[ff.x] = ff.kind === "count" ? Math.round(val) : val; const p = NAPC.forward(m, X16(v)).S[E.out]; lo = Math.min(lo, p); hi = Math.max(hi, p); } return hi - lo; });
    const idx = FS.map((f, i) => i).filter((i) => FS[i]);
    barChart($("#imp"), { labels: idx.map((i) => FS[i].label.replace("Idle history ", "").replace("Last wake: ", "wake: ").replace("Wakes in last ", "wakes ").replace("Time to next timer", "next timer").replace(" (latest)", "").slice(0, 16)), vals: idx.map((i) => imp[i]), rot: true, height: 210, vfmt: (v) => v.toFixed(2) + " range of P" });
  }, 0);
}

function renderPredict(root) {
  const m = mdl(); root.replaceChildren();
  const left = h("div", { class: "card" }, h("h3", {}, "Conditions"), presetPills(), featureSliders(() => upd()));
  const right = h("div", {}, canvasCard("Predicted survival function", "Probability that the idle lasts at least t (one point per octave). The dashed line is the time to the next timer.", "surv"), canvasCard("Predicted distribution of the idle length", "Probability mass per octave bin.", "bins"), h("div", { class: "card", id: "predtxt" }));
  root.append(h("div", { class: "grid" }, left, right));
  function upd() {
    const r = NAPC.forward(m, X16()), p = NAPC.binProbs(r.S), xs = Array.from({ length: D.NOUT }, (_, o) => D.FIRST + o);
    lineChart($("#surv"), { xs, series: [{ ys: Array.from(r.S), color: css("--acc"), dots: true }], xticks: timeTicks(9, 24, 3), ymin: 0, ymax: 1, marker: Math.min(S.v[0], 24), height: 210 });
    barChart($("#bins"), { labels: ["<" + fmtT(gridT(0)).replace(" ", ""), ...xs.slice(1).map((v) => fmtT(Math.pow(2, v)).replace(" ", "")), "tail"], vals: Array.from(p), rot: true, height: 200, vfmt: (v) => v.toFixed(2) });
    const st = stStates();
    $("#predtxt").replaceChildren(h("h3", {}, "Reading"), h("p", {}, "Expected idle length: ", h("b", {}, fmtT(NAPC.expectedIdle(r.S))), " (next timer in ", h("b", {}, fmtT(Math.pow(2, S.v[0]))), ")."),
      h("table", {}, h("tr", {}, h("th", {}, "State"), h("th", {}, "target residency"), h("th", {}, "P(idle ≥ target)")), st.slice(1).map((s) => { const t = Math.log2(s.target) - D.FIRST; const i = Math.max(0, Math.min(D.NOUT - 1, t)); const lo = Math.floor(i), fr = i - lo; const pr = t <= 0 ? 1 - (1 - r.S[0]) * Math.pow(2, t) : (lo + 1 < D.NOUT ? r.S[lo] * (1 - fr) + r.S[lo + 1] * fr : r.S[D.NOUT - 1]); return h("tr", {}, h("td", {}, s.name), h("td", {}, fmtT(s.target)), h("td", {}, (100 * pr).toFixed(1) + " %")); })));
  }
  upd();
}

function renderDecide(root) {
  const m = mdl(); root.replaceChildren();
  const tbl = h("table", {}, h("tr", {}, ["State", "target residency µs", "exit latency µs", "relative power"].map((x) => h("th", {}, x))));
  S.states.forEach((s, i) => tbl.append(h("tr", {}, h("td", {}, s.name), ...["target", "exit", "pow"].map((k) => h("td", {}, h("input", { type: "number", step: k === "pow" ? 0.01 : 1, value: s[k], on: { change: (e) => { s[k] = +e.target.value; render(); } } }))))));
  const num = (label, key, step) => h("div", { class: "row" }, h("label", {}, label), h("input", { type: "number", step, value: S[key], on: { change: (e) => { S[key] = +e.target.value; render(); } } }), h("span"));
  const lam = h("input", { type: "range", min: -3, max: 3, step: 0.1, value: Math.log10(S.lam) }), lo = h("output", {}, S.lam.toPrecision(3));
  lam.addEventListener("input", () => { S.lam = Math.pow(10, +lam.value); lo.textContent = S.lam.toPrecision(3); upd(); });
  const left = h("div", { class: "card" }, h("h3", {}, "Conditions and parameters"), presetPills(), featureSliders(() => upd()), h("h3", { style: "margin-top:12px" }, "Idle states and costs"), tbl,
    num("Energy cost of stopping the tick (ns-eq)", "cs", 500), num("Energy cost of a tick wake (ns-eq)", "cw", 500), num("TICK_NSEC (kernel tick), ns", "tickKernel", 100000),
    h("div", { class: "row" }, h("label", {}, "λ  (energy ↔ latency exchange rate)"), lam, lo));
  const right = h("div", {}, h("div", { class: "card", id: "cands" }), canvasCard("Which choice wins, by time to next timer and λ", "Other conditions as set on the left. The ring marks the current point. λ is what the controller adapts so that the lost share of time stays within the budget: a larger λ means latency is weighted more, so shallower states win.", "dmap", h("div", { class: "legend", id: "dleg", style: "margin-top:6px" })));
  root.append(h("div", { class: "grid" }, left, right));
  function upd() {
    const st = stStates(), r = NAPC.forward(m, X16()), d = NAPC.decide(r.S, st, dopt()), mxv = Math.max(...d.cand.filter((c) => c.allowed).map((c) => Math.abs(c.v)), 1);
    const tb = h("table", {}, h("tr", {}, ["Choice", "E[energy]", "E[avoidable latency]", "E + λ·L (lower wins)"].map((x) => h("th", {}, x))));
    for (const c of d.cand) tb.append(h("tr", { class: c === d.best ? "best" : "" }, h("td", {}, statLabel(st, c) + (c === d.best ? "  ◀ chosen" : "") + (c.allowed ? "" : "  (not allowed: timer closer than a tick)")), h("td", {}, c.allowed ? c.E.toFixed(0) : "–"), h("td", {}, c.allowed ? fmtT(c.L) : "–"), h("td", {}, c.allowed ? (-c.v).toFixed(0) : "–")));
    $("#cands").replaceChildren(h("h3", {}, "Candidates at this point"), tb);
    // decision map
    const cols = [], sl = []; for (let v = 10; v <= 27; v += 0.5) { sl.push(v); } const rowsN = 25, lamV = Array.from({ length: rowsN }, (_, i) => Math.pow(10, -3 + (6 * i) / (rowsN - 1)));
    const cats = new Map(), grid = Array.from({ length: rowsN }, () => new Array(sl.length).fill(-1)); const catList = [];
    sl.forEach((sv, c) => { const v = S.v.slice(); v[0] = sv; const rr = NAPC.forward(m, X16(v)); lamV.forEach((lv, r) => { const dd = NAPC.decide(rr.S, st, { ...dopt(Math.pow(2, sv)), lam: lv }); const key = dd.best.k * 2 + (dd.best.stop ? 1 : 0); if (!cats.has(key)) { cats.set(key, catList.length); catList.push(key); } grid[r][c] = cats.get(key); }); });
    catList.sort((a, b) => a - b); const remap = new Map(catList.map((k, i) => [cats.get(k), i])); for (const row of grid) row.forEach((v, i) => (row[i] = remap.get(v)));
    const colors = catList.map((k) => (k & 1 ? shade(PAL[(k >> 1) % PAL.length], 0.62) : PAL[(k >> 1) % PAL.length]));
    const cur = { c: Math.round((Math.min(27, Math.max(10, S.v[0])) - 10) / 0.5), r: Math.round(((Math.log10(S.lam) + 3) / 6) * (rowsN - 1)) };
    catMap($("#dmap"), grid, { colors, height: 300, xlabel: "time to next timer →", mark: cur, rowTicks: [0, 6, 12, 18, 24].map((i) => ({ i, label: "λ " + lamV[i].toPrecision(1) })), colTicks: [0, 6, 12, 18, 24, 30].filter((i) => i < sl.length).map((i) => ({ i, label: fmtT(Math.pow(2, sl[i])).replace(" ", "") })) });
    $("#dleg").replaceChildren(...catList.map((k, i) => h("span", {}, h("i", { style: "background:" + colors[i] }), st[k >> 1].name + (k & 1 ? " + stop tick" : ""))));
  }
  upd();
}

function renderCompare(root) {
  root.replaceChildren(); const A = S.models.A, B = S.models.B;
  if (!B) { root.append(h("div", { class: "card" }, h("p", {}, "Load a second weight file (header, top right) to compare it with the built-in default: weight differences, predictions and decisions side by side. A state file made by ", h("code", {}, "napctl export"), " also works; pick the CPU in the header."))); return; }
  const grid = h("div", { class: "grid" }, h("div", { class: "card" }, h("h3", {}, "Conditions"), presetPills(), featureSliders(() => upd())));
  const right = h("div", {}, canvasCard("Survival functions", "A (blue) and B (orange) at these conditions.", "cs"), h("div", { class: "card", id: "cd" }), canvasCard("Difference of the time-feature tables, A − B", "Same layout as the Embeddings tab for the selected time feature.", "cdiff", h("div", { class: "note" }, "Time feature: ", h("select", { id: "cdt", on: { change: (e) => { S.embed.t = +e.target.value; upd(); } } }, NAPC.TI.map((xi, t) => h("option", { value: t, ...(t === S.embed.t ? { selected: "" } : {}) }, NAPC.FEATURES[xi].replace(/ \(log2 ns\)/, "")))))));
  grid.append(right); root.append(grid);
  function upd() {
    const ra = NAPC.forward(A, X16()), rb = NAPC.forward(B, X16()), st = stStates(); const xs = Array.from({ length: D.NOUT }, (_, o) => D.FIRST + o);
    lineChart($("#cs"), { xs, series: [{ ys: Array.from(ra.S), color: css("--acc"), dots: true, label: "A" }, { ys: Array.from(rb.S), color: css("--acc2"), dots: true, label: "B" }], xticks: timeTicks(9, 24, 3), ymin: 0, ymax: 1, marker: Math.min(S.v[0], 24), height: 200 });
    const da = NAPC.decide(ra.S, st, dopt()), db = NAPC.decide(rb.S, st, dopt());
    $("#cd").replaceChildren(h("h3", {}, "Decision"), h("table", {}, h("tr", {}, h("th", {}, "Model"), h("th", {}, "Chosen"), h("th", {}, "Expected idle")), h("tr", {}, h("td", {}, "A"), h("td", {}, statLabel(st, da.best)), h("td", {}, fmtT(NAPC.expectedIdle(ra.S)))), h("tr", {}, h("td", {}, "B"), h("td", {}, statLabel(st, db.best)), h("td", {}, fmtT(NAPC.expectedIdle(rb.S))))),
      h("p", { class: "note" }, "Per-group RMS difference: " + groupVals(A).map(([n, a], i) => { const b = groupVals(B)[i][1]; let s = 0; for (let k = 0; k < a.length; k++) s += (a[k] - b[k]) ** 2; return n.split(" (")[0] + " " + Math.sqrt(s / a.length).toFixed(3); }).join(" · ")));
    const t = S.embed.t, rowsM = Array.from({ length: D.NK }, (_, k) => Array.from({ length: D.NHID }, (_, j) => A.w1[(t * D.NK + k) * D.NHID + j] - B.w1[(t * D.NK + k) * D.NHID + j]));
    heatChart($("#cdiff"), rowsM, { rowLabels: Array.from({ length: D.NK }, (_, k) => fmtT(Math.pow(2, D.FIRST + k)).replace(" ", "")), title: "A − B, " + NAPC.FEATURES[NAPC.TI[t]], height: 26 + D.NK * 14 });
  }
  upd();
}

/* ---------- shell ---------- */
const RENDER = { overview: renderOverview, embed: renderEmbed, predict: renderPredict, decide: renderDecide, compare: renderCompare };
function render() { const root = $("#tab-" + S.tab); for (const [k] of TABS) $("#tab-" + k).classList.toggle("on", k === S.tab); [...$("#nav").children].forEach((b) => b.classList.toggle("on", b.dataset.k === S.tab)); RENDER[S.tab](root); }
function setModels() { const sel = $("#active"); sel.replaceChildren(...["A", "B"].filter((k) => S.models[k]).map((k) => h("option", { value: k, ...(k === S.active ? { selected: "" } : {}) }, k + (S.names[k] ? ": " + S.names[k].slice(0, 28) : "")))); $("#nameB").textContent = S.models.B ? S.names.B : "not loaded"; }
function b64buf(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u.buffer; }
function loadFile(file) {
  const rd = new FileReader(); rd.onload = () => {
    try {
      const st = NAPC.parseState(rd.result);
      if (st) { S.stateFile = st; const cs = $("#cpuSel"); cs.replaceChildren(...st.map((r, i) => h("option", { value: i }, r.cpu))); $("#cpuWrap").hidden = false; S.models.B = st[0].model; S.names.B = file.name + " (CPU " + st[0].cpu + ")"; }
      else { S.stateFile = null; $("#cpuWrap").hidden = true; S.models.B = NAPC.parseBlob(rd.result); S.names.B = file.name; }
      setModels(); render();
    } catch (e) { alert("Cannot read this file: " + e.message); }
  }; rd.readAsArrayBuffer(file);
}
function init() {
  S.models.A = NAPC.parseBlob(b64buf(NAP_DEFAULT_BLOB)); $("#nameA").textContent = S.names.A;
  $("#nav").append(...TABS.map(([k, n]) => h("button", { "data-k": k, on: { click: () => { S.tab = k; render(); } } }, n)));
  $("#active").addEventListener("change", (e) => { S.active = e.target.value; render(); });
  $("#cpuSel").addEventListener("change", (e) => { const r = S.stateFile[+e.target.value]; S.models.B = r.model; S.names.B = S.names.B.replace(/\(CPU \d+\)/, "(CPU " + r.cpu + ")"); setModels(); render(); });
  const dz = $("#drop"); $("#file").addEventListener("change", (e) => e.target.files[0] && loadFile(e.target.files[0]));
  ["dragover", "dragenter"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("over"); })); ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, () => dz.classList.remove("over")));
  dz.addEventListener("drop", (e) => { e.preventDefault(); if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]); });
  window.addEventListener("dragover", (e) => e.preventDefault()); window.addEventListener("drop", (e) => { e.preventDefault(); if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]); });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => render()); window.addEventListener("resize", () => { clearTimeout(init.t); init.t = setTimeout(render, 150); });
  setModels(); render();
}
init();

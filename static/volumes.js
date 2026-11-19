// Comprendre : maquettes en volumes (three.js). Aucun chiffre n'est calculé ici hormis les hauteurs (valeur × échelle) :
// les valeurs écrites viennent du serveur, déjà formatées, avec leur lien de source. Caméra orthographique : la hauteur
// est la seule grandeur encodée, sans perspective. Sans WebGL, la légende et le tableau jumeau donnent tout.
import * as THREE from "/static/vendor/three-0.160.0.module.min.js";

const DATA = JSON.parse(document.getElementById("vol-data").textContent);
const T = JSON.parse(document.getElementById("vol-i18n").textContent);
const LANG = document.documentElement.lang || "fr";
const reduce = matchMedia("(prefers-reduced-motion: reduce)");
const dark = matchMedia("(prefers-color-scheme: dark)");

function tokens() {
  const s = getComputedStyle(document.documentElement);
  const g = (n) => s.getPropertyValue(n).trim();
  return { paper: g("--paper"), paper2: g("--paper-2"), ink: g("--ink"), ink2: g("--ink-2"), rule: g("--rule"),
           muted: g("--muted"), accent: g("--accent"), gap: g("--gap"), ok: g("--ok"),
           s0: g("--s0"), s1: g("--s1"), s2: g("--s2"), s3: g("--s3") };
}

function webgl() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); }
  catch { return false; }
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const ease = (t) => 1 - Math.pow(1 - t, 3);
const pt = (serie, an) => serie.points[String(an)];

// --- Géométries partagées : fût à section arrondie (étiré en hauteur) + chapeau biseauté (jamais étiré). ---
function roundedRect(w, d, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -d / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + d - r); s.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
  s.lineTo(x + r, y + d); s.quadraticCurveTo(x, y + d, x, y + d - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  return s;
}
function shaft(w, d) {
  const g = new THREE.ExtrudeGeometry(roundedRect(w, d, Math.min(w, d) * 0.18), { depth: 1, bevelEnabled: false, curveSegments: 6 });
  g.rotateX(-Math.PI / 2);  // extrusion le long de +y, de 0 à 1
  return g;
}
function cap(w, d) {
  const b = Math.min(w, d) * 0.06;
  const g = new THREE.ExtrudeGeometry(roundedRect(w - 2 * b, d - 2 * b, Math.min(w, d) * 0.14),
    { depth: 0.001, bevelEnabled: true, bevelThickness: b, bevelSize: b, bevelSegments: 4, curveSegments: 6 });
  g.rotateX(-Math.PI / 2);
  return g;
}

// Une colonne : hauteur animable, matière pleine ou translucide (« fantôme »).
class Column {
  constructor(w, d, role, ghost = false) {
    this.role = role; this.ghost = ghost; this.h = 0.0001;
    this.group = new THREE.Group();
    this.mat = ghost
      ? new THREE.MeshPhysicalMaterial({ transparent: true, opacity: 0.16, roughness: 0.1, metalness: 0, depthWrite: false })
      : new THREE.MeshPhysicalMaterial({ roughness: 0.42, metalness: 0, clearcoat: 0.55, clearcoatRoughness: 0.35 });
    this.body = new THREE.Mesh(shaft(w, d), this.mat);
    this.top = new THREE.Mesh(cap(w, d), this.mat);
    for (const m of [this.body, this.top]) { m.castShadow = !ghost; m.receiveShadow = !ghost; this.group.add(m); }
    if (ghost) {
      this.edgeMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.55 });
      this.edges = new THREE.LineSegments(new THREE.EdgesGeometry(shaft(w, d), 30), this.edgeMat);
      this.group.add(this.edges);
    }
    this.set(0.0001);
  }
  set(h) {
    this.h = Math.max(h, 0.0001);
    this.body.scale.y = this.h;
    this.top.position.y = this.h;
    if (this.edges) this.edges.scale.y = this.h;
  }
  color(c) { this.mat.color.set(c); if (this.edgeMat) this.edgeMat.color.set(c); }
}

// --- Une scène : rendu à la demande, étiquettes HTML, rotation au doigt, léger balancement au repos. ---
const stages = [];
class Stage {
  constructor(el, build) {
    this.el = el; this.labels = []; this.tweens = []; this.visible = false; this.dirty = true;
    this.az = -0.5; this.el0 = 0.42; this.drag = 0; this.t0 = performance.now();
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.appendChild(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -100, 100);
    this.hemi = new THREE.HemisphereLight(0xffffff, 0xffffff, 1.15);
    this.sun = new THREE.DirectionalLight(0xffffff, 1.7);
    this.sun.position.set(-4, 9, 6);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(1024, 1024);
    this.sun.shadow.radius = 6;
    this.sun.shadow.bias = -0.0005;
    this.scene.add(this.hemi, this.sun, this.sun.target);
    this.floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.ShadowMaterial({ opacity: 0.16 }));
    this.floor.rotation.x = -Math.PI / 2;
    this.floor.receiveShadow = true;
    this.scene.add(this.floor);
    this.ticks = new THREE.Group();
    this.scene.add(this.ticks);
    this.spec = build(this);  // { bounds: {w, h, d}, ticks: [[y, texte]], update(an), recolor(tk) }
    for (const [y, t] of this.spec.ticks) this.tick(y, t);
    const sh = this.sun.shadow.camera, b = this.spec.bounds, r = Math.max(b.w, b.h) + 3;
    Object.assign(sh, { left: -r, right: r, top: r, bottom: -r, near: 0.1, far: 40 });
    sh.updateProjectionMatrix();
    this.recolor();
    this.resize();
    new ResizeObserver(() => this.resize()).observe(el);
    new IntersectionObserver(([e]) => { this.visible = e.isIntersecting; this.dirty = true; loop(); }).observe(el);
    this.pointer();
    stages.push(this);
  }
  recolor() {
    const tk = tokens();
    this.hemi.color.set(tk.paper); this.hemi.groundColor.set(tk.paper2);
    for (const l of this.ticks.children) l.material.color.set(tk.rule);
    this.spec.recolor(tk);
    this.dirty = true;
  }
  resize() {
    const w = this.el.clientWidth, h = this.el.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.aspect = w / h;
    this.dirty = true; loop();
  }
  fit() {  // cadre la boîte englobante (et la place des étiquettes) dans la vue, quel que soit l'angle
    const b = this.spec.bounds, m = this.camera.matrixWorldInverse, v = new THREE.Vector3();
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const x of [-b.w / 2 - 0.3, b.w / 2 + 0.3]) for (const y of [0, b.h]) for (const z of [-b.d / 2, b.d / 2]) {
      v.set(x, y, z).applyMatrix4(m);
      x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x); y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
    }
    // Marges en pixels : graduations à gauche, valeurs au-dessus, années en dessous.
    this.tickW = this.tickW || Math.max(0, ...this.labels.filter((l) => l.left).map((l) => l.d.offsetWidth));
    const W = this.el.clientWidth, H = this.el.clientHeight, L = this.tickW + 18, R = 14, Tp = 40, B = 30;
    const s = Math.max((x1 - x0) / Math.max(W - L - R, 40), (y1 - y0) / Math.max(H - Tp - B, 40));
    const left = x0 - L * s - ((W - L - R) * s - (x1 - x0)) / 2, bottom = y0 - B * s - ((H - Tp - B) * s - (y1 - y0)) / 2;
    Object.assign(this.camera, { left, right: left + W * s, bottom, top: bottom + H * s });
    this.camera.updateProjectionMatrix();
  }
  pointer() {
    let x0 = null, d0 = 0;
    this.el.addEventListener("pointerdown", (e) => { x0 = e.clientX; d0 = this.drag; });
    this.el.addEventListener("pointermove", (e) => {
      if (x0 === null) return;
      this.drag = Math.max(-0.7, Math.min(0.7, d0 + (e.clientX - x0) / 260));
      this.dirty = true; loop();
    });
    const up = () => { x0 = null; };
    this.el.addEventListener("pointerup", up); this.el.addEventListener("pointercancel", up);
    this.el.addEventListener("pointerleave", up);
  }
  tick(v, text) {  // trait horizontal sur le mur du fond + son étiquette
    const b = this.spec.bounds, y = v;
    const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-b.w / 2 - 0.25, y, -b.d / 2 - 0.05),
                                                       new THREE.Vector3(b.w / 2 + 0.25, y, -b.d / 2 - 0.05)]);
    this.ticks.add(new THREE.Line(g, new THREE.LineBasicMaterial({ transparent: true, opacity: 0.9 })));
    this.label(text, null, () => new THREE.Vector3(-b.w / 2 - 0.25, y, -b.d / 2 - 0.05), "is-tick", true);
  }
  label(html, small, anchor, cls = "", left = false) {
    const d = document.createElement("div");
    d.className = "vol-lab " + cls;
    d.setAttribute("aria-hidden", "true");
    this.el.appendChild(d);
    const l = { d, anchor, left, set: (h, s) => { d.innerHTML = esc(h) + (s ? `<small>${esc(s)}</small>` : ""); } };
    l.set(html, small);
    this.labels.push(l);
    return l;
  }
  tween(from, to, apply, ms = 650) {
    if (reduce.matches) { apply(to); this.dirty = true; loop(); return; }
    this.tweens.push({ from, to, apply, t: performance.now(), ms });
    loop();
  }
  frame(now) {
    let active = false;
    this.tweens = this.tweens.filter((tw) => {
      const k = Math.min(1, (now - tw.t) / tw.ms);
      tw.apply(tw.from + (tw.to - tw.from) * ease(k));
      active = active || k < 1;
      return k < 1;
    });
    const sway = reduce.matches ? 0 : Math.sin((now - this.t0) / 4200) * 0.07;
    const az = this.az + this.drag + sway, el = this.el0, b = this.spec.bounds;
    const target = new THREE.Vector3(0, b.h / 2, 0);
    this.camera.position.set(target.x + Math.sin(az) * Math.cos(el) * 20, target.y + Math.sin(el) * 20,
                             target.z + Math.cos(az) * Math.cos(el) * 20);
    this.camera.lookAt(target);
    this.camera.updateMatrixWorld();
    this.fit();
    this.renderer.render(this.scene, this.camera);
    const w = this.el.clientWidth, h = this.el.clientHeight, v = new THREE.Vector3();
    for (const l of this.labels) {
      v.copy(l.anchor()).project(this.camera);
      const side = l.d.classList.contains("is-side") ? (l.anchor().x < 0 ? "left" : "right") : null;
      l.d.style.transform = `translate(${((v.x + 1) / 2) * w}px, ${((1 - v.y) / 2) * h}px) ` +
        (l.left || side === "left" ? "translate(-100%, -50%) translateX(-6px)"
          : side === "right" ? "translate(0, -50%) translateX(6px)" : "translate(-50%, -100%) translateY(-6px)");
    }
    this.dirty = false;
    return active || !reduce.matches;  // au repos, le balancement continue tant que la scène est visible
  }
}

let raf = 0;
function loop() {
  if (raf) return;
  raf = requestAnimationFrame((now) => {
    raf = 0;
    let again = false;
    for (const s of stages) if (s.visible && !document.hidden && (s.dirty || s.tweens.length || !reduce.matches)) again = s.frame(now) || again;
    if (again) loop();
  });
}
document.addEventListener("visibilitychange", loop);

// Pas « joli » pour les graduations : 1, 2, 2,5 ou 5 × 10^n.
function step(max, n = 4) {
  const raw = max / n, p = Math.pow(10, Math.floor(Math.log10(raw)));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw);
}
function graduations(max, k, fmt) {
  const s = step(max), out = [];
  for (let v = s; v <= max + 1e-9; v += s) out.push([v * k, fmt(v)]);
  return out;
}
const pct = (v) => new Intl.NumberFormat(LANG, { maximumFractionDigits: 0 }).format(v) + " %";
const md = (v) => new Intl.NumberFormat(LANG, { maximumFractionDigits: 0 }).format(v / 1000) + (LANG === "fr" ? " Md€" : " bn €");

// --- 1. Recettes, dépenses et solde (part du PIB) ---
function sceneEq(st) {
  const { TR, TE, B9 } = DATA.eq, H = 3;
  const max = Math.max(...DATA.annees.map((a) => Math.max(pt(TR, a).v, pt(TE, a).v)));
  const k = H / max, W = 1.15, D = 1.15, X = 0.78;
  const rec = new Column(W, D, "s1"), dep = new Column(W, D, "ink2");
  rec.group.position.x = -X; dep.group.position.x = X;
  const slab = new Column(W * 1.02, D * 1.02, "gap", true);
  st.scene.add(rec.group, dep.group, slab.group);
  // Valeur au sommet de la colonne la plus haute ; la plus basse porte la sienne sur le côté extérieur, et le solde
  // s'écrit au-dessus de l'écart translucide.
  const haut = (c, x) => () => c.isLow ? new THREE.Vector3(x + Math.sign(x) * (W / 2 + 0.08), c.h, D / 2)
                                       : new THREE.Vector3(x, c.h + 0.12, 0);
  const lr = st.label("", null, haut(rec, -X)), ld = st.label("", null, haut(dep, X));
  const ls = st.label("", null, () => new THREE.Vector3(slab.group.position.x, slab.group.position.y + slab.h + 0.12, 0), "is-hot");
  let cur = null;
  return {
    bounds: { w: 2 * X + W, h: H, d: D },
    ticks: graduations(max, k, pct),
    update(an) {
      const r = pt(TR, an), d = pt(TE, an), b = pt(B9, an);
      const from = cur || { r: 0, d: 0 };
      const lowX = r.v <= d.v ? -X : X;
      slab.group.position.x = lowX;
      rec.isLow = r.v <= d.v; dep.isLow = !rec.isLow;
      lr.d.classList.toggle("is-side", rec.isLow); ld.d.classList.toggle("is-side", dep.isLow);
      st.tween(0, 1, (t) => {
        const hr = (from.r + (r.v - from.r) * t) * k, hd = (from.d + (d.v - from.d) * t) * k;
        rec.set(hr); dep.set(hd);
        slab.group.position.y = Math.min(hr, hd); slab.set(Math.abs(hr - hd));
      });
      cur = { r: r.v, d: d.v };
      lr.set(r.t); ld.set(d.t); ls.set(b.t);
      slab.role = b.v < 0 ? "gap" : "ok"; this.recolor(tokens());
    },
    recolor(tk) { rec.color(tk.s1); dep.color(tk.ink2); slab.color(tk[slab.role]); },
  };
}

// --- 2. Qui dépense ? (euros) : l'ensemble en fantôme, les trois sous-secteurs pleins ---
function sceneSect(st) {
  const ids = DATA.secteurs, H = 3, W = 0.9, D = 0.9, gapX = 1.2;
  const max = Math.max(...DATA.annees.flatMap((a) => ids.map((s) => pt(DATA.sect[s], a).v)));
  const k = H / max, roles = ["ink2", "s1", "s2", "s3"];
  const cols = ids.map((s, i) => {
    const c = new Column(i === 0 ? W * 1.15 : W, i === 0 ? D * 1.15 : D, roles[i], i === 0);
    c.group.position.x = (i - (ids.length - 1) / 2) * gapX;
    st.scene.add(c.group);
    c.lab = st.label("", null, () => new THREE.Vector3(c.group.position.x, c.h + 0.12, 0), i === 0 ? "" : "");
    return c;
  });
  let cur = null;
  return {
    bounds: { w: (ids.length - 1) * gapX + W * 1.15, h: H, d: D * 1.15 },
    ticks: graduations(max, k, md),
    update(an) {
      const vals = ids.map((s) => pt(DATA.sect[s], an));
      const from = cur || vals.map(() => 0);
      st.tween(0, 1, (t) => cols.forEach((c, i) => c.set((from[i] + (vals[i].v - from[i]) * t) * k)));
      cur = vals.map((p) => p.v);
      cols.forEach((c, i) => c.lab.set(vals[i].t));
    },
    recolor(tk) { cols.forEach((c) => c.color(tk[c.role])); },
  };
}

// --- 3. La dette, année après année : une colonne par année, l'année choisie avancée et colorée ---
function sceneDette(st) {
  const GD = DATA.dette, ans = DATA.annees, H = 5.5, gapX = 0.34, W = 0.24, D = 0.7;  // rangée longue : plus haute
  const max = Math.max(...ans.map((a) => pt(GD, a).v)), k = H / max;
  const cols = ans.map((a, i) => {
    const c = new Column(W, D, "s0");
    c.group.position.x = (i - (ans.length - 1) / 2) * gapX;
    c.set(pt(GD, a).v * k);
    st.scene.add(c.group);
    return c;
  });
  const hot = st.label("", null, () => { const c = cols[sel]; return new THREE.Vector3(c.group.position.x, c.h + 0.12, c.group.position.z); }, "is-hot");
  for (const i of [0, Math.floor((ans.length - 1) / 2), ans.length - 1]) {
    const c = cols[i];
    const l = st.label(String(ans[i]), null, () => new THREE.Vector3(c.group.position.x, -0.05, D / 2 + 0.25), "is-tick");
    l.d.style.marginTop = "0";
  }
  let sel = ans.length - 1;
  return {
    bounds: { w: (ans.length - 1) * gapX + W, h: H, d: D },
    ticks: graduations(max, k, pct),
    update(an) {
      const i = ans.indexOf(Number(an)), prev = sel;
      sel = i;
      cols.forEach((c, j) => { c.role = j === i ? "s1" : "s0"; });
      st.tween(0, 1, (t) => { cols[prev].group.position.z = prev === i ? 0.35 : 0.35 * (1 - t); cols[i].group.position.z = 0.35 * t; }, 420);
      hot.set(pt(GD, an).t);
      this.recolor(tokens());
    },
    recolor(tk) { cols.forEach((c) => c.color(tk[c.role])); },
  };
}

// --- Légendes : valeur, mention « provisoire » et lien de source de l'année affichée ---
function legend(an) {
  for (const el of document.querySelectorAll("[data-v]")) {
    const [scene, code] = el.dataset.v.split(".");
    const serie = scene === "dette" ? DATA.dette : DATA[scene][code];
    const p = pt(serie, an);
    el.innerHTML = `<b class="vol-v">${esc(p.t)}</b>` + (p.prov ? ` <span class="prov" title="${esc(T.prov_t)}">${esc(T.prov)}</span>` : "") +
      ` <a class="src" href="/${LANG}/montant/${p.m}" title="${esc(T.src_t)}">${esc(T.src)}</a>`;
  }
  for (const el of document.querySelectorAll("[data-an]")) el.textContent = an;
}

// --- Démarrage ---
const form = document.querySelector("[data-vol-an]");
const range = form.querySelector("input[type=range]"), out = form.querySelector("output");
const builders = { eq: sceneEq, sect: sceneSect, dette: sceneDette };
const live = [];
if (webgl()) {
  for (const el of document.querySelectorAll(".vol-stage[data-scene]")) {
    const st = new Stage(el, builders[el.dataset.scene]);
    live.push(st);
  }
} else {
  for (const el of document.querySelectorAll(".vol-stage")) el.hidden = true;
}

let annee = Number(range.value);
function show(an, push = true) {
  annee = Number(an);
  range.value = annee; out.textContent = annee; range.setAttribute("aria-valuetext", annee);
  for (const st of live) st.spec.update(annee);
  legend(annee);
  if (push) history.replaceState(null, "", `?annee=${annee}`);
}
range.addEventListener("input", () => show(range.value));
form.addEventListener("submit", (e) => { e.preventDefault(); show(range.value); });
show(annee, false);

// Lecture : parcourt les années publiées ; repart du début si l'on est à la fin.
const play = form.querySelector("[data-vol-play]");
let timer = 0;
play.hidden = false;
play.addEventListener("click", () => {
  if (timer) { clearInterval(timer); timer = 0; play.setAttribute("aria-pressed", "false"); play.textContent = T.lecture; return; }
  const ans = DATA.annees;
  if (annee >= ans[ans.length - 1]) show(ans[0]);
  play.setAttribute("aria-pressed", "true"); play.textContent = T.pause;
  timer = setInterval(() => {
    const i = ans.indexOf(annee);
    if (i >= ans.length - 1) { play.click(); return; }
    show(ans[i + 1]);
  }, reduce.matches ? 900 : 750);
});

dark.addEventListener("change", () => live.forEach((s) => s.recolor()));

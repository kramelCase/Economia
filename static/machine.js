// La machine des comptes publics (three.js), en trois étages : en haut les recettes par catégorie, au milieu les trois
// sous-secteurs des administrations (un réservoir chacun), en bas les dépenses par fonction ; à droite, la dette de
// l'ensemble des administrations, en étages par secteur détenteur. Chaque tuyau relie une catégorie à un sous-secteur,
// ou un sous-secteur à une fonction : sa section (aire) est proportionnelle au montant publié pour ce sous-secteur.
// Les sous-secteurs se versent aussi de l'argent entre eux : leurs montants ne s'additionnent pas pour donner l'ensemble.
// Les noms et montants sont rangés dans des bandeaux autour de la scène (haut, bas, droite), reliés par un trait fin à
// ce qu'ils nomment : ils ne couvrent pas le dessin.
import * as THREE from "/static/vendor/three-0.160.0.module.min.js";
import { maquette, biseau, charger } from "/static/maquettes.js?v=11";
await charger();

const DATA = JSON.parse(document.getElementById("mc-data").textContent);
const T = JSON.parse(document.getElementById("mc-i18n").textContent);
const LANG = document.documentElement.lang || "fr";
const reduce = matchMedia("(prefers-reduced-motion: reduce)");
const defile = matchMedia("(max-width: 699px)");  // écran étroit : la scène défile au doigt au lieu de tourner
const dark = matchMedia("(prefers-color-scheme: dark)");
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const ease = (t) => 1 - Math.pow(1 - t, 3);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const svg = (ico, s = 16) => `<svg viewBox="0 0 24 24" width="${s}" height="${s}" aria-hidden="true" fill="none" stroke="currentColor" ` +
  `stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${DATA.svg[ico] || ""}</svg>`;
const nomCourt = (k) => DATA.courts[k] || DATA.noms[k] || k;
// Écart entre deux fins d'année, calculé par ce site (signé, en Md€).
const ecart = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + new Intl.NumberFormat(LANG, { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(Math.abs(v) / 1000) + (LANG === "fr" ? " Md€" : " bn €");
const ACT = DATA.acteurs;  // [{code, nom, ico}] : centrales, locales, sécurité sociale
const NIV = { decouverte: "decouverte", exploration: "exploration", analyse: "analyse" };
const DEC_F = DATA.decF || 6;
let niveau = new URLSearchParams(location.search).get("niveau") || NIV.decouverte;
if (!Object.values(NIV).includes(niveau)) niveau = NIV.decouverte;
const md = (v) => new Intl.NumberFormat(LANG, { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(v / 1000) + (LANG === "fr" ? " Md€" : " bn €");

function sortiesDec(d) {
  const s = [...d.sorties].sort((a, b) => b.v - a.v);
  if (s.length <= DEC_F) return { list: s, top: new Set(s.map((x) => x.k)) };
  const keep = s.slice(0, DEC_F);
  const top = new Set(keep.map((x) => x.k));
  const rest = s.slice(DEC_F);
  const v = rest.reduce((a, x) => a + x.v, 0);
  if (v <= 0) return { list: keep, top };
  return { list: [...keep, { k: "AUTRES_FN", v, m: null, prov: rest.some((x) => x.prov), t: md(v) }], top };
}

function fluxSecteur(s, f, topFn) {
  if (f.k === "AUTRES_FN") {
    const rest = s.sorties.filter((x) => !topFn.has(x.k));
    const v = rest.reduce((a, x) => a + x.v, 0);
    if (v <= 0) return null;
    return { v, k: "AUTRES_FN", t: md(v), m: null, prov: rest.some((x) => x.prov) };
  }
  const x = s.sorties.find((y) => y.k === f.k);
  return x && x.v > 0 ? x : null;
}

function tokens() {
  const s = getComputedStyle(document.documentElement), g = (n) => s.getPropertyValue(n).trim();
  return { paper: g("--paper"), paper2: g("--paper-2"), ink: g("--ink"), ink2: g("--ink-2"), muted: g("--muted"),
           accent: g("--accent"), gap: g("--gap"), ok: g("--ok"), a: [g("--s1"), g("--s2"), g("--s3")] };
}
function webgl() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); }
  catch { return false; }
}

// --- Échelles communes à toutes les années et à tous les tuyaux ---
const ANS = DATA.annees;
const flux = ANS.flatMap((a) => Object.values(DATA.ans[a].secteurs).flatMap((s) =>
  [...s.entrees, ...s.sorties, s.B9].map((x) => Math.abs(x.v))));
const R_MAX = 0.19, KR = R_MAX / Math.sqrt(Math.max(...flux));
const rayon = (v) => KR * Math.sqrt(Math.abs(v));
const ETALON = 1e5;  // tuyau étalon : 100 Md€ (montants en millions)
const GD_MAX = Math.max(...ANS.map((a) => DATA.ans[a].GD ? DATA.ans[a].GD.v : 0));

// --- Géométrie (unités de scène) ---
// Maquette à plat, vue en surplomb : tout est posé sur le même plateau, en trois rangées. Au fond les recettes (un
// bâtiment par catégorie), au milieu les trois sous-secteurs, devant les fonctions ; la dette est une tour à droite.
const XA = [-4.6, 0, 4.6], ZA = [0, 0, 0];          // un bâtiment par sous-secteur
const XB = XA;
const SC = 2.0;                                     // échelle des bâtiments des sous-secteurs
const TOWER = { x: 8.4, z: -4.2, r: 0.85, h: 3.6 }; // dette de l'ensemble
const BACK = -8.8, ROW = 5.4;                       // rangée des recettes (fond), rangée des fonctions (devant)
const PLAT = { x0: -9.6, x1: 11.9, z0: -10.2, z1: 7.6 };

const stage = document.querySelector("[data-mc-stage]");
const tip = stage.querySelector("[data-mc-tip]");
const form = document.querySelector("[data-mc-an]");
const range = form.querySelector("input[type=range]"), out = form.querySelector("output");
let annee = Number(range.value);

class Machine {
  constructor(el) {
    this.el = el; this.labels = []; this.pipes = []; this.tmp = []; this.tweens = []; this.visible = false; this.dirty = true;
    this.az = -0.1; this.elev = 0.38; this.drag = 0; this.t0 = performance.now();  // isométrique : élévation arctan(1/√2)
    this.marge = { t: 120, b: 70, r: 180 };
    // Zoom (1 = toute la scène) et décalage du centre de vue, en unités de la caméra ; sur écran étroit on ouvre zoomé.
    this.zoom = defile.matches ? 3.2 : 1; this.pan = { x: 0, y: 0 }; this.upp = 1;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.prepend(this.renderer.domElement);
    // Traits de rappel entre un bandeau et ce qu'il nomme.
    this.traits = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this.traits.setAttribute("class", "mc-traits"); this.traits.setAttribute("aria-hidden", "true");
    this.traits.innerHTML = `<path class="mc-trait"/><path class="mc-point"/>`;
    el.appendChild(this.traits);
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -100, 100);
    this.hemi = new THREE.HemisphereLight(0xffffff, 0xffffff, 1.25);
    this.sun = new THREE.DirectionalLight(0xffffff, 1.5);
    this.sun.position.set(-5, 12, 9);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.radius = 10;
    this.sun.shadow.bias = -0.0006;
    Object.assign(this.sun.shadow.camera, { left: -11, right: 11, top: 10, bottom: -10, near: 0.5, far: 40 });
    this.scene.add(this.hemi, this.sun);
    // Matières « illustration » : aplats ombrés (toon), verre léger pour les réservoirs.
    const toon = (o = {}) => new THREE.MeshToonMaterial(o);
    this.mats = {
      glass: new THREE.MeshPhysicalMaterial({ transparent: true, opacity: 0.13, roughness: 0.05, depthWrite: false, side: THREE.DoubleSide }),
      metal: toon(), plinth: toon(), plinth2: toon(),
      act: [0, 1, 2].map(() => toon()), actPipe: [0, 1, 2].map(() => new THREE.MeshStandardMaterial({ transparent: true, opacity: 0.6, roughness: 0.2, depthWrite: false })),
      liq: [0, 1, 2].map(() => toon({ transparent: true, opacity: 0.7 })),
      src: toon(), fn: toon(), emp: toon({ transparent: true, opacity: 0.7, depthWrite: false }), empB: toon(),
      exc: toon({ transparent: true, opacity: 0.7, depthWrite: false }), etalon: toon({ transparent: true, opacity: 0.7 }),
      det: [0, 1, 2, 3, 4, 5].map(() => toon()),
      // Maquettes : peinture mate (lumière physique), vitres un peu brillantes et éclairées de l'intérieur.
      maq: Object.fromEntries(Object.entries({ mur: "#eee4d0", toitPlat: "#8a8478", toit: "#b4583c", bleu: "#2f5f9e",
        blanc: "#f8f5ee", rouge: "#c2412f", vert: "#4a8a55", pierre: "#ddd3c0", pierre2: "#c9bea9", brique: "#b5674c",
        bois: "#7a5636", peau: "#e3b48f", or: "#c9a23f", feuille: "#5f9a5a", feuille2: "#7fb26a", pelouse: "#a9c48a" })
        .map(([k, c]) => [k, new THREE.MeshStandardMaterial({ color: c, roughness: 0.82, metalness: 0, flatShading: k.startsWith("feuille") })])
        .concat([["vitre", new THREE.MeshStandardMaterial({ color: "#36475a", roughness: 0.25, metalness: 0.1, emissive: "#ffcf7a", emissiveIntensity: 0.16 })],
                 ["gyro", new THREE.MeshStandardMaterial({ color: "#3a7bd5", emissive: "#3a7bd5", emissiveIntensity: 0.5, roughness: 0.3 })]])),
      grain: new THREE.MeshBasicMaterial(), shadow: new THREE.ShadowMaterial({ opacity: 0.13 }),
    };
    this.build();
    this.niveau = niveau;
    this.recolor();
    this.resize();
    new ResizeObserver(() => this.resize()).observe(el);
    new IntersectionObserver(([e]) => { this.visible = e.isIntersecting; this.dirty = true; loop(); }).observe(el);
    this.pointer();
  }

  mesh(geo, mat, pos, shadow = true, list = null) {
    const m = new THREE.Mesh(geo, mat);
    if (pos) m.position.copy(pos);
    m.castShadow = shadow; m.receiveShadow = true;
    this.scene.add(m);
    if (list) list.push(m);
    return m;
  }
  ring(r, y, x, z, t, mat = this.mats.metal, list = null) {
    const m = this.mesh(new THREE.TorusGeometry(r, t, 10, 64), mat, V(x, y, z), true, list);
    m.rotation.x = Math.PI / 2;
    return m;
  }

  // Une plaque plane fixée devant une structure, qui porte un nom peint (texture) : plus lisible qu'une bande courbe.
  plaque(w, h, pos) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ transparent: true }));
    m.position.copy(pos);
    m.userData.taille = [w, h];
    this.scene.add(m);
    return m;
  }
  // Enseigne posée au-dessus d'une structure : un texte sans fond ni support, qui reste tourné vers
  // le spectateur (rotation autour de la verticale seulement).
  panneau(w, h, pos) {
    const p = this.plaque(w, h, pos);
    p.material.side = THREE.DoubleSide;
    (this.panneaux ||= []).push(p);
    return p;
  }
  ecrire(p, texte, fond) {
    const [w, h] = p.userData.taille;
    p.material.map = this.peint(texte, fond, w, h); p.material.needsUpdate = true;
  }
  // Texture d'une enseigne : une ou plusieurs lignes de texte sur fond transparent.
  peint(texte, fond, w, h) {
    const cle = texte + fond + w + h;
    this.textures ||= new Map();
    if (this.textures.has(cle)) return this.textures.get(cle);
    const c = document.createElement("canvas"), W = 1024, H = Math.round(W * h / w), g = c.getContext("2d");
    c.width = W; c.height = H;
    const col = new THREE.Color(fond), lum = 0.2126 * col.r + 0.7152 * col.g + 0.0722 * col.b;
    // Fond arrondi à la couleur de l'entité, en transparence : on devine la scène derrière ; texte clair ou foncé selon le fond.
    g.fillStyle = fond; g.globalAlpha = 0.72; g.beginPath(); g.roundRect(4, 4, W - 8, H - 8, Math.min(H * 0.22, 60)); g.fill();
    g.globalAlpha = 1;
    const encre = lum > 0.5 ? "#1d1b16" : "#ffffff";
    const police = getComputedStyle(document.body).fontFamily;
    // Une ligne, ou deux coupées au mot le plus central si le nom serait trop petit sur une seule.
    const L = W * 0.9, taille = (lignes, max) => {
      let px = Math.round(max);
      do { g.font = `700 ${px}px ${police}`; px -= 2; } while (Math.max(...lignes.map((l) => g.measureText(l).width)) > L && px > 20);
      return px + 2;
    };
    let lignes = [texte], px = taille(lignes, H * 0.58), tailles;
    if (texte.includes("\n")) {
      // Plusieurs lignes imposées : le nom en gras, puis les montants un peu plus petits.
      lignes = texte.split("\n");
      px = taille(lignes, H * 0.72 / lignes.length);
      tailles = lignes.map((_, k) => (k ? Math.round(px * 0.86) : px));
    } else {
      const mots = texte.split(" ");
      if (px < H * 0.4 && mots.length > 1) {
        let best = 1;
        for (let i = 1; i < mots.length; i++) if (Math.abs(mots.slice(0, i).join(" ").length - texte.length / 2) < Math.abs(mots.slice(0, best).join(" ").length - texte.length / 2)) best = i;
        lignes = [mots.slice(0, best).join(" "), mots.slice(best).join(" ")];
        px = taille(lignes, H * 0.36);
      }
      tailles = lignes.map(() => px);
    }
    g.textAlign = "center"; g.textBaseline = "middle";
    const tot = tailles.reduce((s, t) => s + t * 1.22, 0);
    let y = (H - tot) / 2;
    lignes.forEach((l, k) => {
      g.font = `${k ? 500 : 700} ${tailles[k]}px ${police}`;
      g.fillStyle = encre; g.fillText(l, W / 2, y + tailles[k] * 0.66); y += tailles[k] * 1.22;
    });
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
    this.textures.set(cle, t);
    return t;
  }

  build() {
    this.bandes = [];
    // Plateau rectangulaire en deux épaisseurs et ombre portée.
    const P = PLAT, pw = P.x1 - P.x0, pd = P.z1 - P.z0, pc = V((P.x0 + P.x1) / 2, 0, (P.z0 + P.z1) / 2);
    this.mesh(biseau(pw, 0.24, pd), this.mats.plinth, V(pc.x, -0.12, pc.z), false);
    this.mesh(biseau(pw - 0.6, 0.03, pd - 0.6), this.mats.plinth2, V(pc.x, 0.0, pc.z), false);
    const sh = this.mesh(new THREE.PlaneGeometry(40, 40), this.mats.shadow, V(0, 0.025, 0), false);
    sh.rotation.x = -Math.PI / 2;

    // Les trois acteurs : un bâtiment posé sur une dalle à leur couleur, leur nom sur un pupitre devant.
    this.lAct = ACT.map((a, i) => {
      const x = XB[i], z = ZA[i];
      this.mesh(biseau(2.6, 0.08, 2.0), this.mats.act[i], V(x, 0.04, z));
      const mq = maquette(a.code, this.M());
      mq.position.set(x, 0.1, z - 0.15); mq.scale.setScalar(SC);
      this.scene.add(mq);
      // Enseigne à sa couleur plantée sur le toit : nom, recettes et dépenses publiées du sous-secteur.
      const haut = new THREE.Box3().setFromObject(mq).max.y;
      return { mq, p: this.panneau(2.6, 0.92, V(x, haut + 0.55, z - 0.1)) };
    });

    // Tour de dette de l'ensemble : verre, un anneau tous les 1 000 Md€, étages par détenteur (ou un seul étage
    // avant 2020, années sans ventilation publiée).
    const T0 = TOWER;
    this.mesh(new THREE.CylinderGeometry(T0.r, T0.r, T0.h, 64, 1, true), this.mats.glass, V(T0.x, T0.h / 2, T0.z), false);
    this.ring(T0.r, T0.h, T0.x, T0.z, 0.04);
    this.mesh(new THREE.CylinderGeometry(T0.r + 0.08, T0.r + 0.12, 0.16, 64), this.mats.metal, V(T0.x, 0.08, T0.z));
    for (let v = 1e6; v < GD_MAX; v += 1e6) this.ring(T0.r + 0.01, 0.16 + (v / GD_MAX) * (T0.h - 0.16), T0.x, T0.z, 0.012);
    this.etages = [0, 1, 2, 3, 4, 5].map((k) => {
      const m = this.mesh(new THREE.CylinderGeometry(T0.r * 0.93, T0.r * 0.93, 1, 64), this.mats.det[k], V(T0.x, 0, T0.z));
      m.scale.y = 0.001; m.visible = false;
      // Plaque du détenteur, à droite de la tour, à la hauteur de son étage (écartée des voisines si besoin).
      const b = this.panneau(2.3, 0.56, V(T0.x + T0.r + 1.4, 0, T0.z));
      b.visible = false;
      return { mesh: m, bande: b, y: 0.16, h: 0 };
    });
    this.pTour = this.panneau(1.9, 0.7, V(T0.x, T0.h + 0.5, T0.z));

    // Tuyau étalon : la section d'un tuyau de 100 Md€, pour lire les autres.
    const re = rayon(ETALON);
    const et = this.mesh(new THREE.CylinderGeometry(re, re, 1.1, 32), this.mats.etalon, V(10.6, re + 0.04, 6.4));
    et.rotation.z = Math.PI / 2;
    this.label(`<span class="mc-t">${esc(T.etalon)}</span>`, () => V(10.6, -0.05, 6.4), "is-etalon is-sous");

    // Repères des notions : 1 flux, 2 solde, 3 stock. Un toucher ouvre leur explication (liste de la page) en bulle.
    this.num = [1, 2, 3].map((n) => this.label(`${n}`, () => this.ancreNum[n - 1], "is-num"));
    const notions = [...document.querySelectorAll("[data-mc-notions] > li")];
    this.num.forEach((l, k) => {
      const d = l.d, li = notions[k];
      if (!li) return;
      d.removeAttribute("aria-hidden"); d.setAttribute("role", "button"); d.tabIndex = 0;
      d.setAttribute("aria-label", li.querySelector("strong").textContent);
      for (const ev of ["pointerdown", "pointerup"]) d.addEventListener(ev, (e) => e.stopPropagation());
      const ouvrir = () => {
        const deja = d.classList.contains("is-ouvert");
        this.num.forEach((x) => x.d.classList.remove("is-ouvert"));
        if (deja) { tip.hidden = true; return; }
        const r = d.getBoundingClientRect(), s = this.el.getBoundingClientRect();
        tip.innerHTML = li.innerHTML; tip.classList.add("is-notion");
        tip.style.left = `${Math.max(160, Math.min(s.width - 160, r.left - s.left + r.width / 2))}px`; tip.style.top = `${r.bottom - s.top}px`;
        tip.hidden = false; d.classList.add("is-ouvert");
      };
      d.addEventListener("click", ouvrir);
      d.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ouvrir(); } });
    });
    this.ancreNum = [V(0, 0, 0), V(0, 0, 0), V(T0.x - T0.r - 0.2, T0.h * 0.75, T0.z + 0.3)];

    // Grains : un maillage instancié pour tous les tuyaux.
    this.grains = new THREE.InstancedMesh(new THREE.SphereGeometry(0.05, 10, 8), this.mats.grain, 4000);
    this.grains.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.grains.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(4000 * 3), 3);
    this.scene.add(this.grains);
    this.bounds = { x0: PLAT.x0 + 0.5, x1: PLAT.x1 - 0.3, y0: 0, y1: 2.6, z0: PLAT.z0 + 1, z1: PLAT.z1 - 0.4 };  // serré : les bords du plateau peuvent sortir du cadre
  }

  clear() {
    for (const o of this.tmp) { this.scene.remove(o); o.geometry.dispose(); }
    for (const l of this.labels.filter((l) => l.tmp)) l.d.remove();
    this.labels = this.labels.filter((l) => !l.tmp);
    this.tmp = []; this.pipes = [];
  }

  setNiveau(n) {
    if (n === this.niveau || !Object.values(NIV).includes(n)) return;
    this.niveau = niveau = n;
    this.update(annee);
  }

  bandeau(html, anchor, cls) {
    return this.label(html, anchor, cls, true);
  }

  // Niveau Découverte : les noms et montants vont dans des bandeaux (sans chevaucher la scène).
  etiquetteRecette(pos, item, role) {
    const nom = item.k === "B9" ? (item.v < 0 ? T.emprunt : T.excedent) : item.k === "AUTRES" ? T.autres : nomCourt(item.k);
    const ico = DATA.ico[item.k] || "point";
    const cls = role === "emp" ? "is-emp" : role === "exc" ? "is-exc" : "is-src";
    const html = `<span class="mc-tete"><span class="mc-i">${svg(ico, 14)}</span><span class="mc-t">${esc(nom)}</span></span><span class="mc-m">${esc(item.t)}</span>`;
    this.bandeau(html, () => V(pos.x, 0.35, pos.z), `is-rail-h ${cls}`);
  }
  etiquetteFonction(end, item) {
    const html = `<span class="mc-i">${svg(DATA.ico[item.k] || "point", 14)}</span><span class="mc-t">${esc(nomCourt(item.k))}</span><b>${esc(item.t)}</b>`;
    this.bandeau(html, () => V(end.x, 0.2, end.z + 0.35), "is-rail-b is-fn");
  }

  // Tout ce qui dépend de l'année : vannes, vasques, tuyaux et leurs bandeaux.
  update(an) {
    const d = DATA.ans[an], S = ACT.map((a) => d.secteurs[a.code]);
    const dec = this.niveau === NIV.decouverte;
    const { list: fns, top: topFn } = dec ? sortiesDec(d) : { list: d.sorties, top: new Set(d.sorties.map((x) => x.k)) };
    this.clear();
    let solde = null;
    const dos = (i, k, n) => V(XB[i] + (k - (n - 1) / 2) * 0.24, 0.4, ZA[i] - 0.8);   // entrées : façade arrière
    const face = (i, k, n) => V(XB[i] + (k - (n - 1) / 2) * 0.2, 0.4, ZA[i] + 0.6);   // sorties : façade avant
    const voie = (i) => 0.32 + i * 0.22;  // chaque sous-secteur a sa hauteur de couloir : les tuyaux se croisent sans se toucher
    let gros = null;  // le plus gros tuyau de recettes porte le repère « flux »

    // Rangée du fond : un bâtiment par catégorie de recettes ; l'étiquette posée dessus dit aussi qui paie, quand
    // c'est publié.
    const src = d.entrees.map((e) => ({ e, mat: this.mats.src, role: "src", detail: (d.detail || {})[e.k] }));
    const nE = src.length, x0 = PLAT.x0 + 1.7, xs = (k) => x0 + k * ((TOWER.x - 1.9 - x0) / Math.max(nE - 1, 1));
    src.forEach(({ e, mat, role, detail }, k) => {
      const pos = V(xs(k), 0, BACK);
      this.source(pos, e, mat, role, detail);
      if (dec) this.etiquetteRecette(pos, e, role);
      S.forEach((s, i) => {
        const x = s.entrees.find((y) => y.k === e.k);
        if (!x || x.v <= 0) return;
        const a = V(pos.x + (i - 1) * 0.26, 0.35, BACK + 0.75), b = dos(i, k, nE);
        const c = this.pipe(x, this.mats.actPipe[i], i, [a, V(a.x, voie(i), BACK + 1.5), V(b.x, voie(i), -1.9), b],
                            { ...x, act: i, cat: e.k });
        if (!gros || x.v > gros.v) gros = { v: x.v, c };
      });
    });
    // Le besoin de financement n'est pas une recette : son bâtiment est à part, sur le côté, et ses tuyaux orange
    // arrivent par le flanc des sous-secteurs, au-dessus des couloirs des recettes, jamais par la façade des recettes.
    {
      const pos = V(PLAT.x0 + 1.4, 0, -2.6), haut = voie(ACT.length - 1) + 0.45, zc = -2.3;
      this.source(pos, { ...d.B9, k: "B9" }, this.mats.empB, d.B9.v < 0 ? "emp" : "exc");
      if (dec) this.etiquetteRecette(pos, { ...d.B9, k: "B9" }, d.B9.v < 0 ? "emp" : "exc");
      S.forEach((s, i) => {
        if (!s.B9 || s.B9.v >= 0) return;
        const a = V(pos.x + 0.9, 0.35, pos.z + (i - 1) * 0.22), b = V(XB[i] - 1.15, 0.4, ZA[i] - 0.55);
        const c = this.pipe(s.B9, this.mats.emp, "emp",
                            [a, V(a.x + 0.6, haut + i * 0.14, zc + (i - 1) * 0.2), V(b.x, haut + i * 0.14, zc + (i - 1) * 0.2), b],
                            { ...s.B9, k: "B9", act: i });
        if (!solde || s.B9.v < solde.v) solde = { v: s.B9.v, c };
      });
    }
    // Rangée de devant : un bâtiment par fonction (six plus « autres » en niveau Découverte).
    const nF = fns.length, xf = (k) => PLAT.x0 + 1.1 + k * ((PLAT.x1 - PLAT.x0 - 2.6) / Math.max(nF - 1, 1));
    fns.forEach((f, k) => {
      const end = V(xf(k), 0.14, ROW);
      this.fonction(end, f, 0);
      if (dec) this.etiquetteFonction(end, f);
      S.forEach((s, i) => {
        const x = fluxSecteur(s, f, topFn);
        if (!x) return;
        const a = face(i, k, nF), ex = end.x + (i - 1) * 0.16;
        this.pipe(x, this.mats.actPipe[i], i, [a, V(a.x, voie(i), 1.4), V(ex, voie(i), ROW - 1.4), V(ex, 0.25, ROW - 0.6)], { ...x, act: i, fn: f.k });
      });
    });
    // Capacité de financement d'un sous-secteur : un tuyau qui sort du bâtiment vers une petite vasque à côté.
    S.forEach((s, i) => {
      if (!s.B9 || s.B9.v <= 0) return;
      const a = V(XB[i] - 1.1, 0.35, ZA[i] - 0.3), end = V(XB[i] - 1.9, 0.14, ZA[i] - 1.3);
      const c = this.pipe(s.B9, this.mats.exc, "exc", [a, V(a.x - 0.3, 0.7, ZA[i] - 0.9), end], { ...s.B9, k: "B9", act: i });
      this.mesh(new THREE.CylinderGeometry(0.22, 0.18, 0.12, 32), this.mats.exc, V(end.x, 0.06, end.z), true, this.tmp);
      if (!solde) solde = { v: s.B9.v, c };
    });
    const topE = V(xs(nE - 1), 1, BACK);
    this.ancreNum[0] = gros ? gros.c.getPointAt(0.45) : V(0, 5, 0);
    this.ancreNum[1] = solde ? solde.c.getPointAt(0.4) : topE.clone();
    this.num[1].d.hidden = !solde;

    // Enseignes des sous-secteurs : nom, recettes et dépenses publiées ; toucher le bâtiment les redonne.
    const tk = tokens();
    ACT.forEach((a, i) => {
      const s = S[i], { mq, p } = this.lAct[i];
      this.ecrire(p, `${DATA.courts[a.code] || a.nom}\n${T.recettes} ${s.TR.t}\n${T.depenses} ${s.TE.t}`, tk.a[i]);
      const it = { k: a.code, adm: true, t: `${T.recettes} ${s.TR.t} · ${T.depenses} ${s.TE.t}` };
      mq.traverse((m) => { if (m.isMesh) m.userData = { item: it }; });
      this.pipes.push({ hit: mq.children, item: it, n: 0 });
    });
    this.tour(d, DATA.ans[an - 1]);
    this.recolor();
    this.dirty = true; loop();
  }

  // La tour : hauteur = dette publiée de l'ensemble ; étages = détenteurs publiés (somme contrôlée au chargement).
  // Chaque détenteur a sa plaque à droite, à la hauteur de son étage ; le total est sur le toit.
  tour(d, prec) {
    const avant = Object.fromEntries(((prec && prec.detenteurs) || []).map((x) => [x.k, x.v]));
    const H = TOWER.h - 0.16, k = (v) => (v / GD_MAX) * H, css = getComputedStyle(document.documentElement);
    const det = d.detenteurs && d.detenteurs.length ? d.detenteurs : null;
    const parts = det ? det : d.GD ? [{ ...d.GD, k: "GD" }] : [];
    let y = 0.16, haut = 0;
    this.etages.forEach((E, n) => {
      const p = parts[n], h = p ? k(p.v) : 0, y0 = y;
      E.mesh.visible = !!p;
      if (p) {
        E.mesh.material = det ? this.mats.det[n] : this.mats.det[5];
        E.mesh.userData = { item: { ...p, det: true } };
        this.pipes.push({ hit: [E.mesh], item: p, n: 0 });
      }
      const plaque = !!(p && det), yb = Math.max(y0 + h / 2, haut + 0.6, 0.4);
      E.bande.visible = plaque;
      if (plaque) {
        haut = yb;
        const v = p.k in avant ? ` · ${ecart(p.v - avant[p.k])}` : "";
        this.ecrire(E.bande, `${nomCourt(p.k)}\n${p.t}${v}`, css.getPropertyValue(`--det-${n}`).trim());
      }
      this.tween(E.h, h, (v) => { E.h = v; E.mesh.scale.y = Math.max(v, 0.001); E.mesh.position.y = y0 + v / 2; });
      E.bande.position.y = yb;
      y += h;
    });
    this.ecrire(this.pTour, `${T.dette}\n${d.GD ? d.GD.t : "—"}`, tokens().ink2);
  }

  // Une catégorie de recettes (ou le déficit public) : son bâtiment sur une dalle à sa couleur, créé une fois ;
  // son enseigne (nom et montant) est plantée sur le toit ; qui paie apparaît au toucher.
  source(pos, item, mat, role, detail) {
    this.maqS ||= {};
    let g = this.maqS[item.k];
    if (!g) {
      g = this.maqS[item.k] = maquette(item.k, this.M());
      g.scale.setScalar(1.6);
      g.position.set(pos.x, 0.06, pos.z);
      const haut = new THREE.Box3().setFromObject(g).max.y;
      const dalle = new THREE.Mesh(biseau(2.3, 0.08, 1.6), mat);
      dalle.position.y = -0.03 / 1.6; dalle.scale.setScalar(1 / 1.6); dalle.receiveShadow = true;
      g.add(dalle);
      this.scene.add(g);
      g.userData.p = this.panneau(2.3, 0.72, V(pos.x, haut + 0.45, pos.z));
    }
    const it = { ...item, ens: true, detail };
    g.traverse((m) => { if (m.isMesh) m.userData = { item: it }; });
    this.pipes.push({ hit: g.children, item: it, n: 0 });
    const nom = item.k === "B9" ? (item.v < 0 ? T.emprunt : T.excedent) : item.k === "AUTRES_FN" ? T.autresFonctions : nomCourt(item.k);
    const tk = tokens();
    if (this.niveau !== NIV.decouverte) this.ecrire(g.userData.p, `${nom}\n${item.t}`, role === "emp" ? tk.gap : role === "exc" ? tk.ok : tk.accent);
    else g.userData.p.visible = false;
  }
  // Une fonction de dépense : sa maquette (créée une fois), sur un socle ; son enseigne (nom et montant de
  // l'ensemble) est plantée sur le toit. Toucher la maquette donne son nom et son montant.
  fonction(end, item) {
    this.maqF ||= {};
    let g = this.maqF[item.k];
    if (!g) {
      g = this.maqF[item.k] = maquette(item.k === "AUTRES_FN" ? "GF01" : item.k, this.M());
      g.scale.setScalar(1.45);
      g.position.set(end.x, 0.06, end.z + 0.2);
      const haut = new THREE.Box3().setFromObject(g).max.y;
      const socle = new THREE.Mesh(new THREE.CylinderGeometry(0.56, 0.6, 0.06, 40), this.mats.plinth2);
      socle.position.y = -0.03; socle.receiveShadow = true;
      g.add(socle);
      this.scene.add(g);
      g.userData.p = this.panneau(1.8, 0.55, V(end.x, 0.3, end.z + 1.7));
    }
    const it = { ...item, ens: true };
    g.traverse((m) => { if (m.isMesh) m.userData = { item: it }; });
    this.pipes.push({ hit: g.children, item: it, n: 0 });
    if (this.niveau !== NIV.decouverte) this.ecrire(g.userData.p, `${nomCourt(item.k)}\n${item.t}`, tokens().paper);
    else g.userData.p.visible = false;
  }
  M() { return { ...this.mats.maq, metal: this.mats.metal, accent: this.mats.src }; }
  pipe(x, mat, role, pts, item) {
    const curve = new THREE.CatmullRomCurve3(pts), r = rayon(x.v);
    const m = this.mesh(new THREE.TubeGeometry(curve, 56, r, 14, false), mat, null, false, this.tmp);
    m.userData = { item };
    const gr = r * 0.6;
    this.pipes.push({ hit: [m], curve, role, item, n: Math.max(2, Math.floor(curve.getLength() / (gr * 4.5 + 0.1))), s: gr / 0.05 });
    return curve;
  }

  recolor() {
    const tk = tokens();
    this.hemi.color.set(tk.paper); this.hemi.groundColor.set(tk.paper2);
    this.mats.glass.color.set(tk.ink); this.mats.metal.color.set(tk.muted);
    this.mats.plinth.color.set(tk.paper2); this.mats.plinth2.color.set(new THREE.Color(tk.paper2).lerp(new THREE.Color(tk.ink), 0.06));
    for (let i = 0; i < 3; i++) for (const k of ["act", "actPipe", "liq"]) this.mats[k][i].color.set(tk.a[i]);
    for (const b of this.bandes) { b.mesh.material.map = this.peint(b.texte, tk.a[b.i], b.w, b.h); b.mesh.material.needsUpdate = true; }
    this.mats.src.color.set(tk.accent); this.mats.fn.color.set(tk.ink2);
    this.mats.emp.color.set(tk.gap); this.mats.empB.color.set(tk.gap); this.mats.exc.color.set(tk.ok); this.mats.etalon.color.set(tk.muted);
    // Étages de la tour : tons de l'encre, du plus foncé (en bas) au plus clair ; le nom est dans le bandeau.
    const s = getComputedStyle(document.documentElement);
    this.mats.det.forEach((m, n) => m.color.set(s.getPropertyValue(`--det-${n}`).trim() || tk.muted));
    const clair = (c) => new THREE.Color(c).lerp(new THREE.Color(tk.paper), 0.35);
    this.col = { 0: clair(tk.a[0]), 1: clair(tk.a[1]), 2: clair(tk.a[2]), emp: clair(tk.gap), exc: clair(tk.ok) };
    this.dirty = true;
  }

  resize() {
    const w = this.el.clientWidth, h = this.el.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.traits.setAttribute("viewBox", `0 0 ${w} ${h}`);
    this.el.classList.toggle("is-etroit", w < 700);
    this.dirty = true; loop();
  }
  fit() {
    const b = this.bounds, m = this.camera.matrixWorldInverse, v = new THREE.Vector3();
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const x of [b.x0, b.x1]) for (const y of [b.y0, b.y1]) for (const z of [b.z0, b.z1]) {
      v.set(x, y, z).applyMatrix4(m);
      x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x); y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
    }
    const W = this.el.clientWidth, H = this.el.clientHeight, P = 8, M = this.marge;
    const s = Math.max((x1 - x0) / Math.max(W - P - M.r, 40), (y1 - y0) / Math.max(H - M.t - M.b, 40));
    const left = x0 - P * s - ((W - P - M.r) * s - (x1 - x0)) / 2, bottom = y0 - M.b * s - ((H - M.t - M.b) * s - (y1 - y0)) / 2;
    // Zoom autour du centre décalé ; le décalage reste dans le cadre de la vue entière.
    const z = this.zoom, mx = W * s / 2 * (1 - 1 / z), my = H * s / 2 * (1 - 1 / z);
    this.pan.x = Math.max(-mx, Math.min(mx, this.pan.x)); this.pan.y = Math.max(-my, Math.min(my, this.pan.y));
    const cx = left + W * s / 2 + this.pan.x, cy = bottom + H * s / 2 + this.pan.y, hw = W * s / 2 / z, hh = H * s / 2 / z;
    Object.assign(this.camera, { left: cx - hw, right: cx + hw, bottom: cy - hh, top: cy + hh });
    this.upp = s / z;
    this.camera.updateProjectionMatrix();
  }
  // Zoome d'un facteur en gardant fixe le point (px, py) de la scène, en pixels depuis son coin haut gauche.
  zoomer(f, px = this.el.clientWidth / 2, py = this.el.clientHeight / 2) {
    const z = Math.max(1, Math.min(6, this.zoom * f)), avant = this.upp, apres = avant * this.zoom / z;
    this.pan.x += (px - this.el.clientWidth / 2) * (avant - apres);
    this.pan.y += (this.el.clientHeight / 2 - py) * (avant - apres);
    this.zoom = z; this.dirty = true; loop();
  }
  reset() { this.zoom = defile.matches ? 3.2 : 1; this.pan = { x: 0, y: 0 }; this.drag = 0; this.dirty = true; loop(); }

  pointer() {
    // Un doigt ou la souris : déplace la vue (zoomée, ou au doigt) ou fait tourner la scène (souris, vue entière) ;
    // deux doigts : pincer pour zoomer ; molette : zoom sous le curseur ; un toucher sans glisser : la fiche.
    const pts = new Map();
    let x0 = null, last = null, d0 = 0, moved = false, pince = 0;
    const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
    const ecart = () => { const [a, b] = [...pts.values()]; return Math.hypot(a.x - b.x, a.y - b.y); };
    this.el.addEventListener("pointerdown", (e) => {
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pts.size === 2) { pince = ecart(); moved = true; return; }
      x0 = e.clientX; last = { x: e.clientX, y: e.clientY }; d0 = this.drag; moved = false;
    });
    this.el.addEventListener("pointermove", (e) => {
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pts.size === 2) {
        const d = ecart(), r = this.el.getBoundingClientRect(), [a, b] = [...pts.values()];
        if (pince) this.zoomer(d / pince, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
        pince = d; return;
      }
      if (x0 === null) return;
      if (Math.abs(e.clientX - x0) > 4 || Math.abs(e.clientY - last.y) > 4) moved = true;
      if (this.zoom > 1.01 || e.pointerType === "touch") {
        this.pan.x -= (e.clientX - last.x) * this.upp; this.pan.y += (e.clientY - last.y) * this.upp;
      } else this.drag = Math.max(-0.6, Math.min(0.6, d0 + (e.clientX - x0) / 260));
      last = { x: e.clientX, y: e.clientY };
      this.dirty = true; loop();
    });
    this.el.addEventListener("wheel", (e) => {
      if (this.zoom <= 1 && e.deltaY > 0) return;  // vue entière : la molette fait défiler la page
      e.preventDefault();
      const r = this.el.getBoundingClientRect();
      this.zoomer(Math.exp(-e.deltaY * 0.0015), e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });
    this.el.addEventListener("pointerup", (e) => {
      const seul = pts.size === 1;
      pts.delete(e.pointerId); pince = 0;
      if (seul && x0 !== null && !moved) {  // un toucher : qui, quoi, combien
        const r = this.el.getBoundingClientRect();
        ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
        ray.setFromCamera(ndc, this.camera);
        const hit = ray.intersectObjects(this.pipes.flatMap((p) => p.hit))[0];
        if (hit) {
          const it = hit.object.userData.item;
          let sens;
          if (it.adm) sens = DATA.courts[it.k];
          else if (it.det) sens = it.k === "GD" ? T.dette : `${T.dette} · ${DATA.noms[it.k]}`;
          else {
            const quoi = it.k === "B9" ? (it.v < 0 ? T.emprunt : T.excedent) : nomCourt(it.cat || it.fn || it.k);
            const qui = it.act !== undefined ? DATA.courts[ACT[it.act].code] : T.ensemble;
            sens = it.cat || (it.k === "B9" && it.v < 0) ? `${quoi} → ${qui}` : it.fn || it.k === "B9" ? `${qui} → ${quoi}` : `${quoi} · ${qui}`;
          }
          tip.classList.remove("is-notion"); this.num.forEach((x) => x.d.classList.remove("is-ouvert"));
          const f = fiche(it);
          tip.classList.toggle("is-fiche", !!f);
          tip.innerHTML = f ? `<button type="button" class="mc-f-x" data-fermer aria-label="${esc(T.fermer)}">×</button>${f}`
            : `${esc(sens)}<b>${esc(it.t)}</b>` + (it.m ? ` ${lien(it.m)}` : "");
          if (f) {  // la fiche s'ouvre au centre de l'écran, entière
            document.body.appendChild(tip); tip.style.left = tip.style.top = "";
          } else {  // le montant d'un tuyau, au point touché
            this.el.appendChild(tip);
            tip.style.left = `${Math.max(150, Math.min(r.width - 150, e.clientX - r.left))}px`;
            tip.style.top = `${e.clientY - r.top}px`;
          }
          tip.hidden = false;
        } else { tip.hidden = true; this.num.forEach((x) => x.d.classList.remove("is-ouvert")); }
      }
      x0 = null;
    });
    for (const ev of ["pointercancel", "pointerleave"]) this.el.addEventListener(ev, (e) => { pts.delete(e.pointerId); x0 = null; pince = 0; });
  }

  label(html, anchor, cls = "", tmp = false) {
    const d = document.createElement("div");
    d.className = "mc-lab " + cls;
    d.setAttribute("aria-hidden", "true");
    this.el.appendChild(d);
    const l = { d, anchor, tmp, set: (h) => { d.innerHTML = h; } };
    l.set(html);
    this.labels.push(l);
    return l;
  }
  tween(from, to, apply, ms = 700) {
    if (reduce.matches) { apply(to); return; }
    this.tweens.push({ from, to, apply, t: performance.now(), ms });
  }

  // Range des étiquettes sur une ligne sans chevauchement, au plus près de leur place voulue (axe x ou y).
  static etaler(items, lo, hi, gap) {
    items.sort((a, b) => a.want - b.want);
    let fin = lo;
    for (const it of items) { it.pos = Math.max(it.want - it.len / 2, fin); fin = it.pos + it.len + gap; }
    let debut = hi;
    for (let i = items.length - 1; i >= 0; i--) {
      const it = items[i];
      it.pos = Math.min(it.pos, debut - it.len); debut = it.pos - gap;
    }
    for (const it of items) it.pos = Math.max(lo, it.pos);
  }

  frame(now) {
    this.tweens = this.tweens.filter((tw) => {
      const k = Math.min(1, (now - tw.t) / tw.ms);
      tw.apply(tw.from + (tw.to - tw.from) * ease(k));
      return k < 1;
    });
    const sway = 0;  // caméra fixe : elle ne bouge que si on la fait tourner
    const az = this.az + this.drag + sway, target = V(0.5, 0.6, 0);
    this.camera.position.set(target.x + Math.sin(az) * Math.cos(this.elev) * 30, target.y + Math.sin(this.elev) * 30,
                             target.z + Math.cos(az) * Math.cos(this.elev) * 30);
    this.camera.lookAt(target);
    for (const p of this.panneaux || []) p.rotation.y = az;  // les enseignes restent face au spectateur
    this.camera.updateMatrixWorld();
    this.fit();

    // Grains : répartis le long de chaque tuyau, ils avancent ensemble (immobiles si mouvement réduit).
    const m = new THREE.Matrix4(), sc = new THREE.Vector3(), q0 = new THREE.Quaternion();
    const phase = reduce.matches ? 0 : ((now - this.t0) / 1000) * 0.04;  // lent : un courant, pas une course
    let i = 0;
    for (const p of this.pipes) {
      for (let j = 0; j < p.n && i < 4000; j++) {
        m.compose(p.curve.getPointAt(((j + 0.5) / p.n + phase) % 1), q0, sc.setScalar(p.s));
        this.grains.setMatrixAt(i, m); this.grains.setColorAt(i, this.col[p.role]); i++;
      }
    }
    this.grains.count = i;
    this.grains.instanceMatrix.needsUpdate = true; if (i) this.grains.instanceColor.needsUpdate = true;
    this.renderer.render(this.scene, this.camera);

    // Étiquettes : sur la scène (noms des réservoirs, repères), ou dans un bandeau avec un trait vers leur point.
    const w = this.el.clientWidth, h = this.el.clientHeight, v = new THREE.Vector3();
    const proj = (l) => { v.copy(l.anchor()).project(this.camera); return [((v.x + 1) / 2) * w, ((1 - v.y) / 2) * h]; };
    const haut = [], bas = [], droite = [];
    let pose = 0;  // hauteur des étiquettes posées sur les bâtiments du fond : la marge du haut leur fait place
    for (const l of this.labels) {
      const c = l.d.classList, [px, py] = proj(l), lw = l.d.offsetWidth, lh = l.d.offsetHeight;
      l.px = px; l.py = py; l.lw = lw; l.lh = lh;
      if (c.contains("is-pose")) { l.d.style.transform = `translate(${Math.max(4, Math.min(w - lw - 4, px - lw / 2))}px, ${Math.max(4, py - lh - 4)}px)`; pose = Math.max(pose, lh + 8); }
      else if (c.contains("is-rail-h")) haut.push({ l, want: px, len: lw });
      else if (c.contains("is-rail-b")) bas.push({ l, want: px, len: lw });
      else if (c.contains("is-rail-d")) droite.push({ l, want: py, len: lh });
      else {
        let x = c.contains("is-sous") ? px - lw / 2 : px - lw / 2, y = c.contains("is-sous") ? py + 4 + (l.rang || 0) * 34 : c.contains("is-num") ? py - lh / 2 : py - lh / 2;
        if (c.contains("is-tour")) y = py - lh - 6;
        x = Math.max(4, Math.min(w - lw - 4, x));
        l.d.style.transform = `translate(${x}px, ${y}px)`;
      }
    }
    Machine.etaler(haut, 6, w - 6, 6);
    Machine.etaler(bas, 6, w - 6, 4);

    Machine.etaler(droite, 8, h - this.marge.b, 4);
    let trait = "", point = "";
    const pt = (x, y) => { point += `M${x - 2.5},${y}a2.5,2.5 0 1,0 5,0a2.5,2.5 0 1,0 -5,0`; };
    let th = 0, tb = 0;
    for (const it of haut) {
      const { l } = it, y = 8, cx = it.pos + l.lw / 2;
      l.d.style.transform = `translate(${it.pos}px, ${y}px)`;
      th = Math.max(th, y + l.lh);
      trait += `M${cx},${y + l.lh}L${cx},${y + l.lh + 8}L${l.px},${l.py - 6}`; pt(l.px, l.py - 6);
    }
    for (const it of bas) {
      const { l } = it, y = h - l.lh - 8, cx = it.pos + l.lw / 2;
      l.d.style.transform = `translate(${it.pos}px, ${y}px)`;
      tb = Math.max(tb, l.lh + 16);
      trait += `M${cx},${y}L${cx},${y - 6}L${l.px},${l.py + 4}`; pt(l.px, l.py + 4);
    }
    for (const it of droite) {
      const { l } = it, y = it.pos, cy = y + l.lh / 2, xd = Math.min(l.px + 34, w - l.lw - 4);
      l.d.style.transform = `translate(${xd}px, ${y}px)`;
      trait += `M${xd},${cy}L${xd - 8},${cy}L${l.px + 2},${l.py}`; pt(l.px + 2, l.py);
    }
    this.traits.querySelector(".mc-trait").setAttribute("d", trait);
    this.traits.querySelector(".mc-point").setAttribute("d", point);
    // Les marges suivent la hauteur réelle des bandeaux (la scène se recadre à l'image suivante).
    const etroit = this.el.classList.contains("is-etroit");
    const lr = Math.max(0, ...droite.map((it) => it.l.lw));
    const nm = { t: Math.max(th, pose) + (etroit ? 16 : 24), b: tb + (etroit ? 14 : 24), r: Math.max(etroit ? 40 : 60, lr * 0.5) };
    if (Math.abs(nm.t - this.marge.t) > 2 || Math.abs(nm.b - this.marge.b) > 2 || Math.abs(nm.r - this.marge.r) > 2) { this.marge = nm; this.dirty = true; }
    const encore = this.dirty;
    this.dirty = false;
    return encore || this.tweens.length > 0 || !reduce.matches;
  }
}

let raf = 0, mc = null;
function loop() {
  if (raf || !mc) return;
  raf = requestAnimationFrame((now) => {
    raf = 0;
    if (mc.visible && !document.hidden && (mc.dirty || mc.tweens.length || !reduce.matches) && mc.frame(now)) loop();
  });
}
document.addEventListener("visibilitychange", loop);

// --- Listes sous le schéma : pictogramme, libellé publié, valeur, mention « provisoire » et source ---
const srcT = document.querySelector(".src")?.textContent || "source";
const provT = document.querySelector(".prov")?.textContent || "provisoire";
const valH = (x) => `<b class="mc-v">${esc(x.t)}</b>` + (x.prov ? ` <span class="prov">${esc(provT)}</span>` : "") +
  (x.m ? ` <a class="src" href="/${LANG}/montant/${x.m}">${esc(srcT)}</a>` : "");

// --- Fiche d'une zone touchée : tout le détail publié de l'année, par sous-secteur, avec ses sources ---
const lien = (m) => `<a class="src" href="/${LANG}/montant/${m}">${esc(srcT)}</a>`;
const ligne = (nom, x, coul = "") => x && x.v !== 0 ? `<li>${coul ? `<i class="mc-sw" style="--c:${coul}"></i>` : ""}<span>${esc(nom)}</span>` +
  `<b>${esc(x.t)}</b>${x.prov ? ` <span class="prov">${esc(provT)}</span>` : ""}${x.m ? lien(x.m) : ""}</li>` : "";
const couls = ["var(--s1)", "var(--s2)", "var(--s3)"];
// Camembert (anneau) d'un montant publié et de ses postes : sept parts au plus, les plus petites regroupées
// (somme calculée). Les parts en % sont calculées par ce site ; les montants et leurs sources sont dans la liste.
function camembert(parts, total) {
  let p = parts.filter((x) => x.v > 0).sort((a, b) => b.v - a.v);
  if (p.length > 7) {
    const reste = p.slice(6), v = reste.reduce((s, x) => s + x.v, 0);
    p = [...p.slice(0, 6), { nom: T.autresPostes, v, t: md(v) }];
  }
  const C = 2 * Math.PI * 38;
  let acc = 0;
  const arcs = p.map((x, i) => {
    const l = (x.v / total) * C, a = `<circle r="38" cx="50" cy="50" fill="none" stroke="var(--pie-${i})" stroke-width="20" ` +
      `stroke-dasharray="${Math.max(l - 1.2, 0.4)} ${C}" stroke-dashoffset="${-acc}" transform="rotate(-90 50 50)"><title>${esc(x.nom)}</title></circle>`;
    acc += l;
    return a;
  }).join("");
  const pc = (v) => new Intl.NumberFormat(LANG, { maximumFractionDigits: 1 }).format((v / total) * 100) + " %";
  return `<div class="mc-pie"><svg viewBox="0 0 100 100" role="img" aria-label="${esc(T.parts)}">${arcs}</svg><ul class="mc-f-l">` +
    p.map((x, i) => `<li><i class="mc-sw" style="--c:var(--pie-${i})"></i><span${x.off ? ` title="${esc(x.off)}"` : ""}>${esc(x.nom)}</span><b>${esc(x.t)}</b>` +
      `<em class="mc-pc">${pc(x.v)}</em>${x.m ? lien(x.m) : ""}</li>`).join("") + `</ul><p class="mc-f-o">${esc(T.parts)}</p></div>`;
}
const cta = (label, corps) => `<button type="button" class="mc-f-cta" data-pie data-label="${esc(label)}" aria-expanded="false">${svg("couches", 14)}<span>${esc(label)}</span></button>` +
  `<div class="mc-f-pie" hidden>${corps}</div>`;
function fiche(it) {
  const d = DATA.ans[annee];
  if (!d || it.cat || it.fn || (it.act !== undefined && !it.adm)) return null;  // un tuyau : l'infobulle courte suffit
  const tete = (nom, off, x) => `<p class="mc-f-t">${esc(nom)}</p>` + (off && off !== nom ? `<p class="mc-f-o">${esc(off)}</p>` : "") +
    (x ? `<p class="mc-f-v"><b>${esc(x.t)}</b>${x.prov ? ` <span class="prov">${esc(provT)}</span>` : ""} ${x.m ? lien(x.m) : ""}</p>` : "");
  const secteurs = (pick, titre = T.parSecteur) => `<p class="mc-f-h">${esc(titre)}</p><ul class="mc-f-l">` +
    ACT.map((a, i) => ligne(DATA.courts[a.code] || a.nom, pick(d.secteurs[a.code]), couls[i])).join("") + "</ul>";
  if (it.adm) {
    const s = d.secteurs[it.k], b = s.B9;
    return tete(DATA.courts[it.k], ACT.find((a) => a.code === it.k)?.nom) + `<ul class="mc-f-l">` + ligne(T.recettes, s.TR) +
      ligne(T.depenses, s.TE) + (b ? ligne(b.v < 0 ? T.emprunt : T.excedent, b) : "") + "</ul>" +
      `<p class="mc-f-h">${esc(T.depenses)}</p><ul class="mc-f-l">` + s.sorties.map((x) => ligne(nomCourt(x.k), x)).join("") + "</ul>";
  }
  if (it.det) {
    const prec = (DATA.ans[annee - 1]?.detenteurs || []).find((x) => x.k === it.k);
    return tete(it.k === "GD" ? T.dette : nomCourt(it.k), it.k === "GD" ? null : DATA.noms[it.k], it) +
      `<p class="mc-f-o">${esc(T.detenue)}</p>` + (prec ? `<p class="mc-f-o" title="${esc(T.variation)}">${esc(ecart(it.v - prec.v))}</p>` : "");
  }
  if (it.k === "B9") return tete(it.v < 0 ? T.deficit : T.excedent, DATA.noms.B9, d.B9) +
    (it.v < 0 ? `<p class="mc-f-o">${esc(T.pasRecette)}</p>` : "") + secteurs((s) => s.B9) + `<p class="mc-f-o">${esc(T.pretes)}</p>`;
  const e = d.entrees.find((x) => x.k === it.k);
  if (e) {
    const dont = (d.detail || {})[it.k] || [];
    return tete(it.k === "AUTRES" ? T.autres : nomCourt(it.k), DATA.noms[it.k], e) +
      (dont.length ? cta(T.voirRec, camembert([...dont.map((x) => ({ ...x, nom: DATA.noms[x.k] || nomCourt(x.k) })),
        { nom: T.reste, v: e.v - dont.reduce((s, x) => s + x.v, 0), t: md(e.v - dont.reduce((s, x) => s + x.v, 0)) }], e.v)) : "") +
      secteurs((s) => s.entrees.find((x) => x.k === it.k));
  }
  let f = d.sorties.find((x) => x.k === it.k);
  if (it.k === "AUTRES_FN") {
    const { top } = sortiesDec(d);
    const agg = d.sorties.filter((x) => !top.has(x.k));
    const v = agg.reduce((a, x) => a + x.v, 0);
    f = v > 0 ? { k: "AUTRES_FN", v, t: md(v), m: null, prov: agg.some((x) => x.prov) } : null;
  }
  // Une fonction : comment l'argent est dépensé (natures : rémunérations, achats, prestations, investissement...),
  // puis à quoi précisément (sous-fonctions COFOG), puis quelle administration le dépense.
  const sf = (d.sousf || {})[it.k] || [], na = (d.natures || {})[it.k] || [];
  if (f) {
    const nom = it.k === "AUTRES_FN" ? T.autresFonctions : nomCourt(it.k);
    const off = it.k === "AUTRES_FN" ? T.autresFonctions : DATA.noms[it.k];
    return tete(nom, off, f) +
      (it.k !== "AUTRES_FN" && na.length ? cta(T.voirDep, camembert(na.map((x) => ({ ...x, nom: nomCourt(x.k.split(".")[1]), off: DATA.noms[x.k] })), f.v)) : "") +
      (it.k !== "AUTRES_FN" && sf.length ? cta(T.voirQuoi, camembert(sf.map((x) => ({ ...x, nom: DATA.noms[x.k] || x.k })), f.v)) : "") +
      (it.k === "AUTRES_FN" ? `<p class="mc-f-o">${esc(T.autresFonctions)}</p>` : "") +
      secteurs((s) => (it.k === "AUTRES_FN" ? fluxSecteur(s, f, sortiesDec(d).top) : s.sorties.find((x) => x.k === it.k)), T.quiDepense) +
      (DATA.fiches[it.k] ? `<p class="mc-f-o"><a href="/${LANG}/theme/${DATA.fiches[it.k]}">${esc(T.voirFiche)} →</a></p>` : "");
  }
  return null;
}
function legend(an) {
  const d = DATA.ans[an];
  for (const el of document.querySelectorAll("[data-v]")) el.innerHTML = d[el.dataset.v] ? valH(d[el.dataset.v]) : "—";
  for (const el of document.querySelectorAll("[data-liste]")) {
    const l = el.dataset.liste.split(".").reduce((o, k) => (o ? o[k] : null), d) || [];
    el.innerHTML = l.map((x) =>
      `<li><span class="mc-li">${svg(DATA.ico[x.k], 16)}${esc(x.k === "AUTRES" ? T.autres : DATA.noms[x.k])}</span> <span>${valH(x)}</span></li>`).join("");
    el.closest("[data-si]")?.toggleAttribute("hidden", !l.length);
  }
  for (const el of document.querySelectorAll("[data-an]")) el.textContent = an;
}

if (webgl()) {
  mc = new Machine(stage);
  for (const ev of ["pointerdown", "pointerup"]) tip.addEventListener(ev, (e) => e.stopPropagation());  // liens de la fiche
  tip.addEventListener("click", (e) => {  // boutons de la fiche : fermer, ouvrir ou fermer le camembert
    if (e.target.closest("[data-fermer]")) { tip.hidden = true; return; }
    const b = e.target.closest("[data-pie]");
    if (!b) return;
    const z = b.nextElementSibling, ouvert = z.hidden;
    z.hidden = !ouvert; b.setAttribute("aria-expanded", String(ouvert));
    b.querySelector("span").textContent = ouvert ? T.masquer : b.dataset.label;
  });
  // La fiche se ferme d'un toucher hors d'elle et de la scène, ou par Échap.
  document.addEventListener("pointerdown", (e) => {
    if (!tip.hidden && tip.classList.contains("is-fiche") && !tip.contains(e.target) && !stage.contains(e.target)) tip.hidden = true;
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") tip.hidden = true; });
  // Zoom : boutons dans le coin de la scène (en plus de la molette et du pincement).
  const zb = document.createElement("div");
  zb.className = "mc-zoom";
  zb.innerHTML = [["+", T.zoomPlus, "plus"], ["−", T.zoomMoins, "moins"], ["⤢", T.zoomTout, "tout"]]
    .map(([s, l, k]) => `<button type="button" data-zoom="${k}" aria-label="${esc(l)}" title="${esc(l)}">${s}</button>`).join("");
  for (const ev of ["pointerdown", "pointerup"]) zb.addEventListener(ev, (e) => e.stopPropagation());
  zb.addEventListener("click", (e) => {
    const k = e.target.closest("[data-zoom]")?.dataset.zoom;
    if (k === "plus") mc.zoomer(1.4); else if (k === "moins") mc.zoomer(1 / 1.4); else if (k === "tout") mc.reset();
  });
  stage.appendChild(zb);
  stage.closest(".mc-fig").classList.add("has-3d");
  const aide = document.createElement("p");
  aide.className = "mc-aide"; aide.textContent = T.glisser;
  stage.parentElement.after(aide);
  const d = stage.parentElement;  // écran étroit : on ouvre la scène sur son centre (les trois administrations)
  d.scrollLeft = (d.scrollWidth - d.clientWidth) / 2;
} else stage.hidden = true;

function show(an, push = true) {
  annee = Number(an);
  range.value = annee; out.textContent = annee; range.setAttribute("aria-valuetext", annee);
  tip.hidden = true;
  if (mc) mc.update(annee);
  legend(annee);
  const q = new URLSearchParams(location.search);
  q.set("annee", annee);
  if (niveau !== NIV.decouverte) q.set("niveau", niveau); else q.delete("niveau");
  if (push) history.replaceState(null, "", `?${q}`);
}
range.addEventListener("input", () => show(range.value));
form.addEventListener("submit", (e) => { e.preventDefault(); show(range.value); });
const nivForm = form.querySelector("[data-mc-niveau]");
nivForm?.addEventListener("change", (e) => {
  const v = e.target.closest("[name=niveau]")?.value;
  if (!v || e.target.disabled) return;
  niveau = v;
  document.querySelectorAll("[name=niveau]").forEach((el) => { el.checked = el.value === v; });
  if (mc) mc.setNiveau(v);
  const q = new URLSearchParams(location.search);
  q.set("niveau", v);
  q.set("annee", annee);
  history.replaceState(null, "", `?${q}`);
});
show(annee, false);

const play = form.querySelector("[data-mc-play]");
let timer = 0;
play.hidden = false;
play.addEventListener("click", () => {
  if (timer) { clearInterval(timer); timer = 0; play.setAttribute("aria-pressed", "false"); play.textContent = T.lecture; return; }
  if (annee >= ANS[ANS.length - 1]) show(ANS[0]);
  play.setAttribute("aria-pressed", "true"); play.textContent = T.pause;
  timer = setInterval(() => {
    const i = ANS.indexOf(annee);
    if (i >= ANS.length - 1) { play.click(); return; }
    show(ANS[i + 1]);
  }, 1100);
});
dark.addEventListener("change", () => mc && mc.recolor());

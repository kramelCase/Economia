// Atelier de graphique (docs/vision/WIDGETS.md, W1). Tout se passe ici : le serveur ne sert que des fichiers
// statiques (un par document, /data/manifest.json). Les paramètres de l'URL sont relus contre des listes fermées ;
// une valeur inconnue est ignorée. Aucun texte saisi n'est inséré en HTML : textContent seulement.
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const L = JSON.parse($("#at-l").textContent);
  const CIT = JSON.parse($("#at-c").textContent);
  const DOCS = JSON.parse($("#at-d").textContent);
  const lang = document.documentElement.lang === "en" ? "en" : "fr";
  const loc = lang === "fr" ? "fr-FR" : "en-GB";
  const root = $("#atelier");
  const form = $("#at-form");
  // Ordre fixe (le JSON du serveur trie ses clés) : le premier type possible sert de repli.
  const TYPES = ["courbe", "aires", "aires100", "barres", "empilees", "pente", "multiples", "chaleur", "classement", "points"];
  const UNE_ANNEE = new Set(["classement", "points"]);
  const EMPILE = new Set(["aires", "aires100", "empilees"]);
  const FORMATS = { carre: [1080, 1080], large: [1200, 675], vertical: [1080, 1920] };
  const MAX_SERIES = 5;
  let doublons = [], sansIndice = [], ruptures = [];
  // Pictogrammes 40 × 28, dessinés en currentColor : ils suivent le thème clair ou sombre.
  const ICONES = {
    courbe: '<polyline points="3,22 11,15 18,18 27,8 37,11" fill="none" stroke-width="2.5"/><polyline points="3,25 13,22 22,23 37,19" fill="none" stroke-width="2.5" opacity=".5"/>',
    aires: '<path d="M3 25 L3 16 L13 12 L22 14 L37 6 L37 25Z" stroke="none" opacity=".45"/><path d="M3 25 L3 21 L13 19 L22 20 L37 16 L37 25Z" stroke="none"/>',
    aires100: '<rect x="3" y="3" width="34" height="22" stroke="none" opacity=".3"/><path d="M3 25 L3 13 L13 11 L22 15 L37 9 L37 25Z" stroke="none" opacity=".6"/><path d="M3 25 L3 20 L13 19 L22 21 L37 18 L37 25Z" stroke="none"/>',
    barres: '<rect x="4" y="12" width="4" height="13" stroke="none"/><rect x="9" y="7" width="4" height="18" stroke="none" opacity=".5"/><rect x="17" y="10" width="4" height="15" stroke="none"/><rect x="22" y="4" width="4" height="21" stroke="none" opacity=".5"/><rect x="30" y="14" width="4" height="11" stroke="none"/><rect x="35" y="9" width="3" height="16" stroke="none" opacity=".5"/>',
    empilees: '<rect x="5" y="15" width="7" height="10" stroke="none"/><rect x="5" y="9" width="7" height="5" stroke="none" opacity=".5"/><rect x="17" y="12" width="7" height="13" stroke="none"/><rect x="17" y="4" width="7" height="7" stroke="none" opacity=".5"/><rect x="29" y="17" width="7" height="8" stroke="none"/><rect x="29" y="10" width="7" height="6" stroke="none" opacity=".5"/>',
    pente: '<line x1="8" y1="4" x2="8" y2="25" stroke-width="1" opacity=".4"/><line x1="32" y1="4" x2="32" y2="25" stroke-width="1" opacity=".4"/><line x1="8" y1="20" x2="32" y2="8" stroke-width="2.5"/><line x1="8" y1="10" x2="32" y2="18" stroke-width="2.5" opacity=".5"/><circle cx="8" cy="20" r="2.5" stroke="none"/><circle cx="32" cy="8" r="2.5" stroke="none"/>',
    multiples: '<rect x="3" y="3" width="15" height="10" fill="none" stroke-width="1" opacity=".5"/><rect x="22" y="3" width="15" height="10" fill="none" stroke-width="1" opacity=".5"/><rect x="3" y="15" width="15" height="10" fill="none" stroke-width="1" opacity=".5"/><rect x="22" y="15" width="15" height="10" fill="none" stroke-width="1" opacity=".5"/><polyline points="5,11 10,7 16,8" fill="none" stroke-width="2"/><polyline points="24,10 29,9 35,5" fill="none" stroke-width="2"/><polyline points="5,22 10,21 16,18" fill="none" stroke-width="2"/><polyline points="24,19 29,22 35,21" fill="none" stroke-width="2"/>',
    chaleur: '<g stroke="none"><rect x="3" y="4" width="8" height="6" opacity=".25"/><rect x="12" y="4" width="8" height="6" opacity=".5"/><rect x="21" y="4" width="8" height="6" opacity=".8"/><rect x="30" y="4" width="8" height="6"/><rect x="3" y="11" width="8" height="6" opacity=".6"/><rect x="12" y="11" width="8" height="6" opacity=".35"/><rect x="21" y="11" width="8" height="6" opacity=".55"/><rect x="30" y="11" width="8" height="6" opacity=".9"/><rect x="3" y="18" width="8" height="6" opacity=".9"/><rect x="12" y="18" width="8" height="6" opacity=".7"/><rect x="21" y="18" width="8" height="6" opacity=".3"/><rect x="30" y="18" width="8" height="6" opacity=".45"/></g>',
    classement: '<g stroke="none"><rect x="3" y="3" width="34" height="4"/><rect x="3" y="9" width="26" height="4" opacity=".8"/><rect x="3" y="15" width="19" height="4" opacity=".65"/><rect x="3" y="21" width="12" height="4" opacity=".5"/></g>',
    points: '<g stroke-width="1" opacity=".35"><line x1="3" y1="5" x2="37" y2="5"/><line x1="3" y1="12" x2="37" y2="12"/><line x1="3" y1="19" x2="37" y2="19"/><line x1="3" y1="26" x2="37" y2="26"/></g><g stroke="none"><circle cx="32" cy="5" r="3"/><circle cx="24" cy="12" r="3"/><circle cx="17" cy="19" r="3"/><circle cx="10" cy="26" r="2.6"/></g>',
    carre: '<rect x="9" y="3" width="22" height="22" rx="1" fill="none" stroke-width="2"/>',
    large: '<rect x="3" y="6" width="34" height="16" rx="1" fill="none" stroke-width="2"/>',
    vertical: '<rect x="13" y="1" width="14" height="26" rx="1" fill="none" stroke-width="2"/>',
    cofog: '<circle cx="20" cy="14" r="10" fill="none" stroke-width="5" opacity=".4"/><path d="M20 4 A10 10 0 0 1 29.5 17" fill="none" stroke-width="5"/>',
    apu: '<rect x="6" y="6" width="9" height="19" stroke="none"/><rect x="18" y="3" width="9" height="22" stroke="none" opacity=".5"/><line x1="30" y1="25" x2="30" y2="14" stroke-width="3"/><line x1="3" y1="25" x2="37" y2="25" stroke-width="1.5"/>',
    "ofgl-region": '<path d="M8 6 L18 3 L30 6 L35 15 L28 25 L14 24 L5 16Z" fill="none" stroke-width="2"/><path d="M18 3 L20 14 L35 15 M20 14 L14 24" fill="none" stroke-width="1" opacity=".5"/>',
    "ofgl-departement": '<path d="M8 6 L18 3 L30 6 L35 15 L28 25 L14 24 L5 16Z" fill="none" stroke-width="2"/><path d="M18 3 L16 10 L24 12 L30 6 M5 16 L16 10 M24 12 L26 19 L14 24 M26 19 L35 15" fill="none" stroke-width="1" opacity=".6"/>',
    "dep-m57": '<path d="M4 6 L11 4 L17 7 L18 15 L12 21 L5 19 L3 12Z" fill="none" stroke-width="2"/><g stroke-width="2.5"><line x1="22" y1="7" x2="37" y2="7"/><line x1="22" y1="13" x2="33" y2="13" opacity=".7"/><line x1="22" y1="19" x2="29" y2="19" opacity=".5"/></g>',
    "dep-m52": '<path d="M4 6 L11 4 L17 7 L18 15 L12 21 L5 19 L3 12Z" fill="none" stroke-width="2" opacity=".6"/><g stroke-width="2.5" opacity=".6"><line x1="22" y1="7" x2="37" y2="7"/><line x1="22" y1="13" x2="33" y2="13"/><line x1="22" y1="19" x2="29" y2="19"/></g>',
  };
  const icone = (k) => `<svg viewBox="0 0 40 28" width="40" height="28" aria-hidden="true" fill="currentColor" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">${ICONES[k] || ""}</svg>`;
  // Une tuile : un vrai bouton radio (clavier, lecteur d'écran), une icône, un libellé court ; le libellé long en titre.
  function tuile(nom, valeur, texte, on, opts = {}) {
    const lab = document.createElement("label");
    lab.className = (opts.classe || "at-tuile") + (on ? " is-on" : "") + (opts.off ? " is-off" : "");
    if (opts.titre) lab.title = opts.titre;
    const c = document.createElement("input");
    c.type = opts.type || "radio"; c.name = nom; c.value = valeur; c.checked = on; c.disabled = !!opts.off;
    lab.appendChild(c);
    if (opts.icone) lab.insertAdjacentHTML("beforeend", icone(opts.icone)); // icônes constantes du code, jamais de texte saisi
    const t = document.createElement("span");
    t.textContent = texte;
    lab.appendChild(t);
    return lab;
  }
  const nf = (d) => new Intl.NumberFormat(loc, { maximumFractionDigits: d, minimumFractionDigits: d });

  let M = null; // manifeste
  const dicos = {};
  const parts = new Map();
  let S = null; // état courant, toujours validé
  let rendu = 0;
  let dernier = null; // { rows, series, unite, sources } du dernier rendu, pour les exports

  async function json(url) {
    const r = await fetch(url, { credentials: "same-origin" });
    if (!r.ok) throw new Error(url + " " + r.status);
    return r.json();
  }
  const doc = () => M.documents[S.doc];
  async function dico(d) {
    if (!dicos[d]) {
      const x = await json("/data/" + M.documents[d].dictionnaire.fichier);
      x.parId = new Map(x.noeuds.map((n) => [n.id, n]));
      for (const e of x.entites) if (L.entites[e.code]) e.nom = L.entites[e.code];
      x.parCode = new Map(x.entites.map((e) => [e.code, e]));
      dicos[d] = x;
    }
    return dicos[d];
  }
  function partie(d, cle) {
    const p = M.documents[d].parties[cle];
    if (!p) return Promise.resolve(null);
    if (!parts.has(p.fichier)) parts.set(p.fichier, json("/data/" + p.fichier).then((x) => ({ ...x, cle })));
    return parts.get(p.fichier);
  }
  const libN = (n) => (lang === "en" && n.en ? n.en : n.fr);

  // --- État : lu dans l'URL, validé contre le manifeste et le dictionnaire du document ---
  function brut() {
    const q = new URLSearchParams(location.search);
    const g = (k) => q.get(k) || "";
    return { doc: g("doc"), u: g("u"), m: g("m"), n: g("n"), e: g("e"), t: g("t"), a0: g("a0"), a1: g("a1"),
             z: g("z"), b: g("b"), titre: g("titre"), st: g("st"), an: g("an"), fmt: g("fmt") };
  }
  function annotations(txt) {
    return String(txt).split(/\n|;/).map((l) => l.match(/^\s*(\d{4})\s*:\s*(.{1,60}?)\s*$/)).filter(Boolean)
      .slice(0, 6).map((m) => ({ a: +m[1], t: m[2] }));
  }
  function valider(r, D) {
    const d = M.documents[r.doc];
    const s = { doc: r.doc };
    s.u = d.unites.includes(r.u) ? r.u : (d.unites.includes("PC_GDP") ? "PC_GDP" : d.unites.includes("EUR_HAB") ? "EUR_HAB" : d.unites[0]);
    s.m = d.mesures.includes(r.m) ? r.m : d.mesures[0];
    const avec = D.noeuds.filter((n) => n.donnees);
    s.n = r.n.split(",").map(Number).filter((i) => D.parId.has(i) && D.parId.get(i).donnees).slice(0, 12);
    if (!s.n.length) s.n = defautsN(r.doc, avec);
    const tousOk = d.niveau === "region" || d.niveau === "departement";
    s.e = r.e === "*" && tousOk ? ["*"] : r.e.split(",").filter((c) => D.parCode.has(c)).slice(0, 12);
    if (!s.e.length) s.e = tousOk ? ["*"] : [D.parCode.has("APU-S13") ? "APU-S13" : D.entites[0].code];
    const [y0, y1] = d.annees;
    const an = (x, def) => (/^\d{4}$/.test(x) && +x >= y0 && +x <= y1 ? +x : def);
    s.a0 = an(r.a0, y0);
    s.a1 = an(r.a1, y1);
    if (s.a0 > s.a1) [s.a0, s.a1] = [s.a1, s.a0];
    s.t = TYPES.includes(r.t) ? r.t : (s.e[0] === "*" ? "classement" : "courbe");
    s.z = r.z !== "0";
    s.b = /^\d{4}$/.test(r.b) && +r.b >= s.a0 && +r.b <= s.a1 ? +r.b : null;
    s.titre = r.titre.slice(0, 120);
    s.st = r.st.slice(0, 160);
    s.an = annotations(r.an);
    s.fmt = FORMATS[r.fmt] ? r.fmt : "carre";
    return s;
  }
  function defautsN(d, avec) {
    const code = (c) => avec.find((n) => n.code === c);
    if (d === "apu") return ["TR", "TE"].map(code).filter(Boolean).map((n) => n.id);
    if (d === "cofog") return ["GF10", "GF07", "GF09"].map(code).filter(Boolean).map((n) => n.id);
    const tot = avec.find((n) => /^D[ée]penses totales/.test(n.fr));
    return [(tot || avec.find((n) => n.niveau <= 1) || avec[0]).id];
  }
  function versUrl(s) {
    const q = new URLSearchParams();
    q.set("doc", s.doc); q.set("u", s.u);
    if (doc().mesures.length > 1) q.set("m", s.m);
    q.set("n", s.n.join(",")); q.set("e", s.e.join(",")); q.set("t", s.t);
    q.set("a0", s.a0); q.set("a1", s.a1);
    if (!s.z) q.set("z", "0");
    if (s.b) q.set("b", s.b);
    if (s.titre) q.set("titre", s.titre);
    if (s.st) q.set("st", s.st);
    if (s.an.length) q.set("an", s.an.map((x) => x.a + ":" + x.t).join(";"));
    if (s.fmt !== "carre") q.set("fmt", s.fmt);
    return location.pathname + "?" + q.toString();
  }

  // --- Garde-fous : un choix impossible est grisé, avec sa raison écrite ---
  function raisons(s, D) {
    const r = {};
    const tous = s.e[0] === "*";
    const nbSeries = s.n.length * (tous ? 1 : s.e.length);
    const p0 = D.parId.get(s.n[0]).parent;
    const freres = s.n.length >= 2 && p0 != null && s.n.every((i) => D.parId.get(i).parent === p0);
    for (const t of TYPES) {
      if (EMPILE.has(t)) {
        if (!doc().empilable || !freres) { r[t] = L.raisons.empiler; continue; }
        if (tous || s.e.length !== 1) { r[t] = L.raisons.une_entite; continue; }
      }
      if (UNE_ANNEE.has(t)) {
        if (!tous && nbSeries < 2) r[t] = L.raisons.deux_series;
        continue;
      }
      if (tous) { r[t] = L.raisons.trop; continue; }
      if (s.a1 <= s.a0) { r[t] = L.raisons.deux_annees; continue; }
      if (nbSeries > MAX_SERIES && t !== "chaleur" && t !== "multiples") r[t] = L.raisons.trop;
    }
    return r;
  }

  // --- Données : on ne charge que les fichiers du choix courant ---
  async function donnees(s, D) {
    const d = doc();
    const cles = d.decoupe === "unite" ? [s.u] : d.decoupe === "noeud_id" ? s.n.map(String) : ["tout"];
    const ps = (await Promise.all(cles.map((c) => partie(s.doc, c)))).filter(Boolean);
    const nSet = new Set(s.n);
    const eSet = s.e[0] === "*" ? null : new Set(s.e);
    const multiM = d.mesures.length > 1;
    const unAn = UNE_ANNEE.has(s.t);
    const rows = [];
    for (const p of ps) {
      const c = p.cols;
      for (let i = 0; i < c.v.length; i++) {
        if (c.u[i] !== s.u || !nSet.has(c.n[i]) || (eSet && !eSet.has(c.e[i])) || (multiM && c.m[i] !== s.m)) continue;
        const a = c.a[i];
        if (unAn ? a !== s.a1 : a < s.a0 || a > s.a1) continue;
        if (s.t === "pente" && a !== s.a0 && a !== s.a1) continue;
        rows.push({ n: c.n[i], e: c.e[i], a, v: c.v[i], id: c.id[i], p: c.p[i], f: p.sources[c.f[i]],
                    siren: c["x:siren"] ? c["x:siren"][i] : null, pop: c["x:population"] ? +c["x:population"][i] : null });
      }
    }
    const varieN = s.n.length > 1;
    const varieE = s.e[0] === "*" || s.e.length > 1;
    for (const r of rows) {
      const nom = libN(D.parId.get(r.n));
      const ent = D.parCode.get(r.e).nom;
      r.s = varieN && varieE ? `${nom} — ${ent}` : varieE ? ent : nom;
    }
    // Plusieurs lignes publiées pour une même série et une même année (anciennes régions avant 2016, DEP-67A…) :
    // le site ne choisit pas et n'additionne pas, il ne trace rien et le signale.
    const nb = new Map();
    for (const r of rows) { const k = r.s + "|" + r.a; nb.set(k, (nb.get(k) || 0) + 1); }
    doublons = [...new Set(rows.filter((r) => nb.get(r.s + "|" + r.a) > 1).map((r) => `${r.s} (${r.a})`))];
    const gardes = rows.filter((r) => nb.get(r.s + "|" + r.a) === 1);
    // Ruptures lues dans les attributs publiés (même règle que le serveur, api/queries.py ruptures_detail) : SIREN qui
    // change, ou population publiée qui varie de plus de moitié. La ligne est coupée (segment) et la note les nomme.
    ruptures = [];
    const parS = new Map();
    for (const r of gardes) parS.set(r.s, [...(parS.get(r.s) || []), r]);
    for (const [nom, rs] of parS) {
      rs.sort((x, y) => x.a - y.a);
      let seg = 0, siren0 = null, pop0 = null;
      for (const r of rs) {
        if ((r.siren && siren0 && r.siren !== siren0) || (r.pop && pop0 && Math.abs(r.pop / pop0 - 1) > 0.5)) {
          seg++;
          ruptures.push(`${nom} (${r.a})`);
        }
        r.seg = seg;
        siren0 = r.siren || siren0; pop0 = r.pop || pop0;
      }
    }
    return gardes;
  }

  // --- Unités d'affichage : l'axe en Md€, M€, € ou %, sans recalcul des valeurs publiées ---
  function echelle(rows, s) {
    if (s.b) return { k: 1, lab: L.t.base100.replace("%(a)s", s.b), fmt: (v) => nf(1).format(v) };
    if (s.t === "aires100") return { k: 1, lab: "%", fmt: (v) => nf(1).format(v) + " %", pct: true };
    if (s.u === "PC_GDP" || s.u === "PC_TOT") return { k: 1, lab: L.unites[s.u], fmt: (v) => nf(1).format(v) + " %" };
    if (s.u === "EUR_HAB") return { k: 1, lab: L.unites[s.u], fmt: (v) => nf(0).format(v) + (lang === "fr" ? " €/hab." : " € per capita") };
    const base = s.u === "MIO_EUR" ? 1e6 : 1;
    const max = Math.max(0, ...rows.map((r) => Math.abs(r.v * base)));
    const [div, suf] = max >= 1e9 ? [1e9, lang === "fr" ? "Md€" : "bn €"] : max >= 1e6 ? [1e6, lang === "fr" ? "M€" : "m €"] : [1, "€"];
    return { k: base / div, lab: `${suf} (${L.unites[s.u]})`, fmt: (v) => nf(1).format(v) + " " + suf };
  }
  // Indice = valeur ÷ valeur de l'année de base × 100. Une base nulle ou négative (un solde) donnerait un indice
  // sans sens ou de signe inversé : ces séries sont retirées et la note les nomme.
  function base100(rows, s) {
    const ref = new Map(rows.filter((r) => r.a === s.b).map((r) => [r.s, r.v]));
    sansIndice = [...new Set(rows.filter((r) => !(ref.get(r.s) > 0)).map((r) => r.s))];
    return rows.filter((r) => ref.get(r.s) > 0).map((r) => ({ ...r, y: (r.v / ref.get(r.s)) * 100 }));
  }

  function couleurs() {
    const cs = getComputedStyle(document.documentElement);
    const v = (k, d) => (cs.getPropertyValue(k).trim() || d);
    return { series: [1, 2, 3, 4, 5].map((i) => v("--s" + i, "#2a78d6")), ink: v("--ink", "#222"),
             muted: v("--muted", "#777"), rule: v("--rule", "#ccc"), paper: v("--paper", "#fff") };
  }

  // --- Le graphique (Observable Plot), même code pour l'écran et pour l'export ---
  function figure(s, rows, ech, series, opt) {
    const P = window.Plot;
    const col = opt.col;
    const color = { domain: series, range: col.series };
    const grid = { grid: true, label: ech.lab, zero: s.z || !(s.t === "courbe" || s.t === "multiples" || s.t === "pente"),
                   tickFormat: ech.pct ? (v) => nf(0).format(v * 100) : (v) => new Intl.NumberFormat(loc).format(v) };
    const x = { label: null, tickFormat: "d" };
    // Axe des années en bandes (barres, chaleur) : une étiquette toutes les 1, 2, 5 ou 10 années, assez pour ne pas
    // se chevaucher (une année s'écrit sur environ trois fois la taille du texte).
    const annees = [...new Set(rows.map((r) => r.a))].sort((a, b) => a - b);
    const pas = [1, 2, 5, 10, 20].find((p) => annees.length / p <= opt.w / (opt.fs * 3.4)) || 20;
    const bandes = { label: null, tickFormat: "d", ticks: annees.filter((a) => a % pas === 0 || annees.length === 1) };
    const ann = s.an.filter((a) => a.a >= s.a0 && a.a <= s.a1);
    const marques = [];
    const annMarques = () => ann.length ? [P.ruleX(ann, { x: "a", stroke: col.muted, strokeDasharray: "4,4" }),
      P.text(ann, { x: "a", text: "t", frameAnchor: "top", textAnchor: "start", dx: 4, dy: 4, fill: col.ink, lineWidth: 12 })] : [];
    const base = { width: opt.w, height: opt.h, marginLeft: opt.ml, marginRight: opt.mr || 16, marginTop: 20, marginBottom: 32,
                   style: { color: col.ink, background: "transparent", fontSize: opt.fs + "px", fontFamily: opt.font }, color };
    const tip = (o) => P.tip(rows, P.pointerX({ ...o, title: (r) => `${r.s}\n${r.a} : ${ech.fmt(r.y)}${r.p ? " (" + L.t.provisoire + ")" : ""}` }));
    switch (s.t) {
      case "courbe":
        return P.plot({ ...base, x, y: grid, marks: [P.ruleY([0], { stroke: col.rule }), ...annMarques(),
          P.lineY(rows, { x: "a", y: "y", stroke: "s", z: (r) => r.s + "|" + (r.seg || 0), strokeWidth: 2.5 }),
          P.dot(rows, P.selectLast({ x: "a", y: "y", fill: "s", z: "s", r: 4 })), opt.tip ? tip({ x: "a", y: "y", stroke: "s" }) : null] });
      case "aires":
      case "aires100":
        return P.plot({ ...base, x, y: grid, marks: [...annMarques(),
          P.areaY(rows, { x: "a", y: "y", fill: "s", order: series, offset: s.t === "aires100" ? "normalize" : null, stroke: col.paper, strokeWidth: 1 }),
          P.ruleY([0], { stroke: col.rule })] });
      case "barres":
        return P.plot({ ...base, x: { axis: null, domain: series }, fx: { ...bandes, padding: 0.15 }, y: grid,
          marks: [P.barY(rows, { fx: "a", x: "s", y: "y", fill: "s", tip: opt.tip }), P.ruleY([0], { stroke: col.rule })] });
      case "empilees":
        return P.plot({ ...base, x: { ...bandes, type: "band" }, y: grid,
          marks: [P.barY(rows, { x: "a", y: "y", fill: "s", order: series, tip: opt.tip }), P.ruleY([0], { stroke: col.rule })] });
      case "classement":
      case "points": {
        const h = Math.max(opt.h, rows.length * opt.ligne + 60);
        const ml = Math.min(opt.w * 0.45, 12 + opt.fs * 0.55 * Math.max(...rows.map((r) => r.s.length)));
        const m = s.t === "classement"
          ? P.barX(rows, { y: "s", x: "y", fill: col.series[0], sort: { y: "-x" }, tip: opt.tip })
          : P.dot(rows, { y: "s", x: "y", fill: col.series[0], r: 5, sort: { y: "-x" }, tip: opt.tip });
        return P.plot({ ...base, height: h, marginLeft: ml, marginRight: (opt.mr || 16) + opt.fs * 1.5, color: undefined,
          y: { label: null }, x: { ...grid, axis: "top", label: null }, // l'unité est dans le sous-titre
          marks: [P.ruleX([0], { stroke: col.rule }), m] });
      }
      case "pente": {
        // Les valeurs sont écrites aux deux bouts : l'axe vertical serait redondant. Étiquettes écartées si elles se chevauchent.
        const ys = rows.map((r) => r.y);
        const lo = grid.zero ? Math.min(0, ...ys) : Math.min(...ys), hi = Math.max(...ys);
        const pas = ((hi - lo) || 1) * (opt.fs * 1.3) / Math.max(60, opt.h - 52);
        const ecarter = (a) => {
          const r = rows.filter((x) => x.a === a).map((x) => ({ ...x, ly: x.y })).sort((u, v) => u.y - v.y);
          for (let i = 1; i < r.length; i++) r[i].ly = Math.max(r[i].ly, r[i - 1].ly + pas);
          return r;
        };
        const ml = 16 + opt.fs * 0.6 * Math.max(...rows.filter((r) => r.a === s.a0).map((r) => ech.fmt(r.y).length));
        return P.plot({ ...base, marginLeft: ml, marginRight: ml, x: { label: null, tickFormat: "d", ticks: [s.a0, s.a1] },
          y: { ...grid, axis: null, grid: false }, marks: [
          P.lineY(rows, { x: "a", y: "y", stroke: "s", z: (r) => r.s + "|" + (r.seg || 0), strokeWidth: 2.5 }),
          P.dot(rows, { x: "a", y: "y", fill: "s", r: 5 }),
          P.text(ecarter(s.a1), { x: "a", y: "ly", text: (r) => ech.fmt(r.y), dx: 10, textAnchor: "start", fill: col.ink }),
          P.text(ecarter(s.a0), { x: "a", y: "ly", text: (r) => ech.fmt(r.y), dx: -10, textAnchor: "end", fill: col.ink })] });
      }
      case "multiples":
        // Le nom de chaque série est écrit dans son panneau (un axe à droite le tronquait).
        return P.plot({ ...base, height: Math.max(opt.h, series.length * 110), x, y: { ...grid, label: null },
          fy: { label: null, domain: series, axis: null, padding: 0.12 }, marks: [P.frame({ stroke: col.rule }),
            P.text(series, { fy: (d) => d, text: (d) => d, frameAnchor: "top-left", dx: 8, dy: 6, fill: col.ink, fontWeight: 600 }),
            P.lineY(rows, { x: "a", y: "y", fy: "s", stroke: "s", z: (r) => r.s + "|" + (r.seg || 0), strokeWidth: 2 }), P.ruleY([0], { stroke: col.rule })] });
      case "chaleur": {
        const ml = Math.min(opt.w * 0.45, 12 + opt.fs * 0.55 * Math.max(...series.map((t) => t.length)));
        return P.plot({ ...base, height: Math.max(160, series.length * opt.ligne * 1.4 + 60), marginLeft: ml,
          x: { ...bandes, type: "band" }, y: { label: null, domain: series },
          // Une teinte, du fond vers la couleur de la première série : lisible en thème clair comme sombre.
          color: { type: "linear", range: [col.rule, col.series[0]], legend: false }, marks: [P.cell(rows, { x: "a", y: "s", fill: "y", inset: 0.5, tip: opt.tip })] });
      }
    }
    return P.plot({ ...base, marks });
  }

  function textes(s, D, ech) {
    const noms = s.n.map((i) => libN(D.parId.get(i)));
    const titre = s.titre || (noms.length === 1 ? noms[0] : L.docs[s.doc]);
    const ents = s.e[0] === "*" ? `${L.t.tous} (${L.docs[s.doc]})` : s.e.map((c) => D.parCode.get(c).nom).join(", ");
    const ans = UNE_ANNEE.has(s.t) ? String(s.a1) : `${s.a0}–${s.a1}`;
    const sous = s.st || [ents, ech.lab, ans].join(" · ");
    return { titre, sous };
  }
  function citation(ids) {
    const out = [...ids].map((i) => CIT[i]).filter(Boolean)
      .map((c) => `${c.editeur}, ${c.titre} (${c.identifiant}${c.maj ? ", " + c.maj : ""})`);
    return (out.length > 1 ? L.t.sources : L.t.source) + " : " + out.join(" ; ");
  }
  function notes(s, rows, ech) {
    const n = [];
    if (s.b && sansIndice.length) n.push(L.t.base_neg + " : " + sansIndice.join(", "));
    if (doublons.length) n.push(L.t.plusieurs + " : " + doublons.join(", "));
    if (ruptures.length) n.push(L.t.rupture + " : " + ruptures.join(", "));
    if (s.an.some((a) => a.a >= s.a0 && a.a <= s.a1)) n.push(L.t.annot);
    if (s.t === "aires100") n.push(L.t.calcul);
    if (!s.z && (s.t === "courbe" || s.t === "multiples" || s.t === "pente")) n.push(L.t.zero);
    if (rows.some((r) => r.p)) n.push(L.t.provisoire + " : " + [...new Set(rows.filter((r) => r.p).map((r) => r.a))].join(", "));
    return n.join(" · ");
  }

  // --- Rendu à l'écran ---
  async function rendre() {
    const jeton = ++rendu;
    const D = await dico(S.doc);
    const rows0 = await donnees(S, D);
    if (jeton !== rendu) return;
    let rows = rows0.map((r) => ({ ...r }));
    const ech = echelle(rows, S);
    sansIndice = [];
    rows = S.b ? base100(rows, S) : rows.map((r) => ({ ...r, y: r.v * ech.k }));
    const series = [...new Set(rows.map((r) => r.s))];
    const t = textes(S, D, ech);
    const cadre = $(".at-cadre");
    cadre.dataset.format = S.fmt;
    $("#at-titre-v").textContent = t.titre;
    $("#at-sous-v").textContent = t.sous;
    const leg = $("#at-leg");
    leg.textContent = "";
    const col = couleurs();
    if (series.length > 1 && !UNE_ANNEE.has(S.t) && S.t !== "chaleur") series.forEach((nom, i) => {
      const li = document.createElement("li");
      const sw = document.createElement("span");
      sw.className = "at-sw";
      sw.style.background = col.series[i % col.series.length];
      li.append(sw, document.createTextNode(nom));
      leg.appendChild(li);
    });
    const plot = $("#at-plot");
    plot.textContent = "";
    const sources = new Set(rows.map((r) => r.f));
    if (!rows.length) {
      plot.textContent = L.t.aucune;
    } else {
      const w = plot.clientWidth || 340;
      const ratio = { carre: 0.75, large: 0.5, vertical: 1.25 }[S.fmt];
      // À l'écran, la hauteur suit le format choisi sans dépasser la fenêtre (le format exact sert à l'export).
      const h = Math.round(Math.max(240, Math.min(w * ratio, window.innerHeight * 0.68)));
      plot.appendChild(figure(S, rows, ech, series, { w, h, ml: 56, fs: 13,
        font: "inherit", col, tip: true, ligne: 22 }));
    }
    $("#at-note").textContent = notes(S, rows, ech);
    $("#at-src").textContent = sources.size ? citation(sources) : "";
    table(rows, ech);
    dernier = { rows, series, ech, sources, t };
  }

  function table(rows, ech) {
    const box = $("#at-table");
    box.textContent = "";
    if (!rows.length) return;
    const tb = document.createElement("table");
    const cap = document.createElement("caption");
    cap.className = "fig-src";
    cap.textContent = citation(new Set(rows.map((r) => r.f)));
    tb.appendChild(cap);
    const th = tb.createTHead().insertRow();
    for (const h of [L.t.serie, L.t.annee, L.t.valeur, ""]) { const c = document.createElement("th"); c.scope = "col"; c.textContent = h; th.appendChild(c); }
    const body = tb.createTBody();
    for (const r of rows.slice(0, 3000)) {
      const tr = body.insertRow();
      tr.insertCell().textContent = r.s;
      tr.insertCell().textContent = r.a;
      tr.insertCell().textContent = ech.fmt(r.y) + (r.p ? " (" + L.t.provisoire + ")" : "");
      const a = document.createElement("a");
      a.className = "src";
      a.href = `/${lang}/montant/${r.id}`;
      a.textContent = L.t.voir;
      tr.insertCell().appendChild(a);
    }
    box.appendChild(tb);
  }

  // --- Export : une image complète (titre, légende, graphique, notes, source, lien) aux formats des réseaux ---
  function lignes(txt, max) {
    // Un mot plus long que la ligne (le lien) est coupé en morceaux.
    const mots = String(txt).split(/\s+/).flatMap((m) => m.match(new RegExp(`.{1,${max}}`, "g")) || []);
    const out = [];
    let l = "";
    for (const m of mots) {
      if ((l + " " + m).trim().length > max && l) { out.push(l); l = m; } else l = (l + " " + m).trim();
    }
    if (l) out.push(l);
    return out;
  }
  function composer() {
    const [W, H] = FORMATS[S.fmt];
    const { rows, series, ech, sources, t } = dernier;
    const col = couleurs();
    const fs = Math.round(W / 40);
    const pad = Math.round(W / 18);
    const font = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("xmlns", NS);
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const el = (n, a, txt) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; svg.appendChild(e); return e; };
    el("rect", { width: W, height: H, fill: col.paper });
    let y = pad;
    const max = (taille, gras) => Math.floor((W - 2 * pad) / (taille * (gras ? 0.6 : 0.53)));
    for (const l of lignes(t.titre, max(fs * 1.9, true))) { y += fs * 1.9; el("text", { x: pad, y, fill: col.ink, "font-family": font, "font-size": fs * 1.9, "font-weight": 700 }, l); }
    for (const l of lignes(t.sous, max(fs))) { y += fs * 1.4; el("text", { x: pad, y, fill: col.muted, "font-family": font, "font-size": fs }, l); }
    y += fs * 0.8;
    if (series.length > 1 && !UNE_ANNEE.has(S.t) && S.t !== "chaleur") {
      let x = pad;
      y += fs * 1.2;
      series.forEach((nom, i) => {
        const w = fs * 1.6 + nom.length * fs * 0.52;
        if (x + w > W - pad) { x = pad; y += fs * 1.5; }
        el("rect", { x, y: y - fs * 0.8, width: fs * 0.9, height: fs * 0.9, rx: 2, fill: col.series[i % col.series.length] });
        el("text", { x: x + fs * 1.2, y, fill: col.ink, "font-family": font, "font-size": fs }, nom);
        x += w + fs;
      });
      y += fs * 0.6;
    }
    const pied = [notes(S, rows, ech), citation(sources), location.origin + versUrl(S)].filter(Boolean);
    const piedL = pied.flatMap((p) => lignes(p, Math.floor((W - 2 * pad) / (fs * 0.8 * 0.62))));
    const hPied = piedL.length * fs * 1.15 + pad;
    const hFig = Math.max(200, H - y - hPied - fs);
    const nb = UNE_ANNEE.has(S.t) ? rows.length : S.t === "chaleur" ? series.length * 1.4 : 1;
    const ligne = Math.min(fs * 2, (hFig - 60) / Math.max(1, nb));
    const fsFig = Math.round(Math.min(fs * 0.85, Math.max(10, ligne * 0.8)));
    const fig = figure(S, rows, ech, series, { w: W - 2 * pad, h: hFig, ml: fs * 3.4, mr: fs, fs: fsFig,
      font, col, tip: false, ligne });
    const g = document.createElementNS(NS, "g");
    g.setAttribute("transform", `translate(${pad},${y})`);
    const figSvg = fig.tagName.toLowerCase() === "svg" ? fig : fig.querySelector("svg");
    // Classement ou points sur 100 départements : le graphique est réduit pour tenir dans l'image.
    const hReel = +figSvg.getAttribute("height");
    if (hReel > hFig) g.setAttribute("transform", `translate(${pad},${y}) scale(${hFig / hReel})`);
    g.appendChild(figSvg);
    svg.appendChild(g);
    let yp = H - pad / 2 - (piedL.length - 1) * fs * 1.15;
    for (const l of piedL) { el("text", { x: pad, y: yp, fill: col.muted, "font-family": font, "font-size": fs * 0.8 }, l); yp += fs * 1.15; }
    return { svg, W, H };
  }
  const nomFichier = (ext) => `comptes-publics-${S.doc}-${S.t}-${S.a1}.${ext}`;
  function telecharger(blob, nom) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = nom;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  function svgTexte() {
    const { svg } = composer();
    return new XMLSerializer().serializeToString(svg);
  }
  function png() {
    return new Promise((ok, ko) => {
      const [W, H] = FORMATS[S.fmt];
      const img = new Image(), url = URL.createObjectURL(new Blob([svgTexte()], { type: "image/svg+xml" }));
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = W; c.height = H;
        c.getContext("2d").drawImage(img, 0, 0, W, H);
        URL.revokeObjectURL(url);
        c.toBlob((b) => (b ? ok(b) : ko(new Error("png"))), "image/png");
      };
      img.onerror = (e) => { URL.revokeObjectURL(url); ko(e); };
      img.src = url;
    });
  }
  function csv() {
    const D = dicos[S.doc];
    const q = (x) => `"${String(x ?? "").replace(/"/g, '""')}"`;
    const head = ["document", "indicateur", "code", "perimetre", "annee", "unite", "valeur", "provisoire", "source", "lien"];
    const out = [head.join(",")];
    for (const r of dernier.rows) {
      const n = D.parId.get(r.n);
      out.push([S.doc, libN(n), n.code, D.parCode.get(r.e).nom, r.a, S.u, r.v, r.p ? 1 : 0, r.f,
        `${location.origin}/${lang}/montant/${r.id}`].map(q).join(","));
    }
    return new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  }
  async function action(act, bouton) {
    if (!dernier || !dernier.rows.length) return;
    if (act === "svg") telecharger(new Blob([svgTexte()], { type: "image/svg+xml" }), nomFichier("svg"));
    if (act === "png") telecharger(await png(), nomFichier("png"));
    if (act === "csv") telecharger(csv(), nomFichier("csv"));
    if (act === "lien") {
      try { await navigator.clipboard.writeText(location.origin + versUrl(S)); bouton.textContent = L.t.copie; } catch (e) { /* lien visible dans la barre d'adresse */ }
    }
    if (act === "partager") {
      const f = new File([await png()], nomFichier("png"), { type: "image/png" });
      const data = { title: dernier.t.titre, url: location.origin + versUrl(S) };
      try { await navigator.share(navigator.canShare && navigator.canShare({ files: [f] }) ? { ...data, files: [f] } : data); } catch (e) { /* annulé */ }
    }
  }

  // --- Réglages : construits depuis le manifeste et le dictionnaire, jamais depuis l'URL ---
  function option(sel, v, txt, on) { const o = document.createElement("option"); o.value = v; o.textContent = txt; o.selected = on; sel.appendChild(o); }
  function remplir(D) {
    const d = doc();
    const f = form.elements;
    const boxD = $('[data-nom="doc"]');
    boxD.textContent = "";
    DOCS.filter((k) => M.documents[k]).forEach((k) => boxD.appendChild(tuile("doc", k, L.docs[k], k === S.doc, { icone: k })));
    const boxU = $('[data-nom="u"]');
    boxU.textContent = "";
    const vus = new Set();
    for (const u of d.unites) {
      const [sym, mot] = L.court[u];
      if (vus.has(sym + mot)) continue;
      vus.add(sym + mot);
      boxU.appendChild(tuile("u", u, `${sym} ${mot}`, u === S.u, { classe: "at-puce", titre: L.unites[u] }));
    }
    $(".at-mesure").hidden = d.mesures.length < 2;
    f.m.textContent = ""; d.mesures.forEach((m) => option(f.m, m, m, m === S.m));
    for (const k of ["a0", "a1", "b"]) {
      const sel = f[k];
      [...sel.options].forEach((o) => { if (o.value) o.remove(); });
      for (let a = d.annees[1]; a >= d.annees[0]; a--) option(sel, a, a, a === (k === "b" ? S.b : S[k]));
    }
    f.z.checked = S.z;
    f.titre.value = S.titre; f.st.value = S.st;
    f.an.value = S.an.map((x) => `${x.a} : ${x.t}`).join("\n");
    const boxF = $('[data-nom="fmt"]');
    boxF.textContent = "";
    Object.keys(FORMATS).forEach((k) => boxF.appendChild(tuile("fmt", k, L.formats[k], k === S.fmt, { icone: k })));
    // Indicateurs : l'arbre du document, indenté par niveau.
    const boxN = $('.at-choix[data-nom="n"]');
    boxN.textContent = "";
    boxN.classList.toggle("is-pastilles", D.noeuds.filter((x) => x.donnees).length <= 16);
    const min = Math.min(...D.noeuds.map((n) => n.niveau));
    for (const n of D.noeuds.filter((x) => x.donnees)) {
      const lab = document.createElement("label");
      lab.style.paddingLeft = (n.niveau - min) * 12 + "px";
      const c = document.createElement("input");
      c.type = "checkbox"; c.name = "n"; c.value = n.id; c.checked = S.n.includes(n.id);
      lab.append(c, document.createTextNode(" " + libN(n)));
      boxN.appendChild(lab);
    }
    const boxE = $('.at-choix[data-nom="e"]');
    boxE.textContent = "";
    boxE.classList.toggle("is-pastilles", D.entites.length <= 16);
    const tousOk = d.niveau === "region" || d.niveau === "departement";
    const ajouter = (v, txt, on) => {
      const lab = document.createElement("label");
      const c = document.createElement("input");
      c.type = "checkbox"; c.name = "e"; c.value = v; c.checked = on;
      lab.append(c, document.createTextNode(" " + txt));
      boxE.appendChild(lab);
    };
    if (tousOk) ajouter("*", `${L.t.tous}`, S.e[0] === "*");
    for (const e of D.entites) ajouter(e.code, (e.insee ? e.insee + " " : "") + e.nom, S.e.includes(e.code));
    types(D);
  }
  // Ce qui est tracé, sous la barre : une étiquette par indicateur et par périmètre, retirée d'un clic ; le nombre
  // de choix s'affiche aussi sur le bouton de chaque menu.
  function selection(D) {
    const ul = $("#at-selection");
    ul.textContent = "";
    const ajouter = (nom, v, txt) => {
      const li = document.createElement("li");
      li.className = "is-" + nom;
      const t = document.createElement("span");
      t.textContent = txt;
      t.title = txt;
      const b = document.createElement("button");
      b.type = "button"; b.dataset.nom = nom; b.dataset.v = v; b.textContent = "×";
      b.setAttribute("aria-label", `${L.t.retirer} : ${txt}`);
      li.append(t, b);
      ul.appendChild(li);
    };
    for (const i of S.n) ajouter("n", i, libN(D.parId.get(i)));
    for (const c of S.e) ajouter("e", c, c === "*" ? `${L.t.tous} (${L.docs[S.doc]})` : D.parCode.get(c).nom);
    // L'état validé peut différer des cases (choix vidé → choix par défaut) : les cases suivent l'état.
    for (const c of form.querySelectorAll('input[name="n"]')) c.checked = S.n.includes(+c.value);
    for (const c of form.querySelectorAll('input[name="e"]')) c.checked = S.e.includes(c.value);
    $('[data-nb="n"]').textContent = S.n.length;
    $('[data-nb="e"]').textContent = S.e[0] === "*" ? L.t.tous : S.e.length;
  }
  $("#at-selection").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-nom]");
    if (!b) return;
    const c = form.querySelector(`input[name="${b.dataset.nom}"][value="${CSS.escape(b.dataset.v)}"]`);
    if (!c) return;
    c.checked = false;
    c.dispatchEvent(new Event("change", { bubbles: true }));
  });
  // Un seul menu ouvert à la fois ; il se ferme en cliquant ailleurs ou avec Échap.
  const pops = [...form.querySelectorAll(".at-pop")];
  for (const p of pops) p.addEventListener("toggle", () => { if (p.open) pops.forEach((o) => { if (o !== p) o.open = false; }); });
  document.addEventListener("click", (ev) => { if (!ev.target.closest(".at-pop")) pops.forEach((p) => { p.open = false; }); });
  document.addEventListener("keydown", (ev) => {
    if (ev.key !== "Escape") return;
    const p = pops.find((x) => x.open);
    if (p) { p.open = false; p.querySelector("summary").focus(); }
  });
  function types(D) {
    const sansBase = EMPILE.has(S.t) || UNE_ANNEE.has(S.t);
    form.elements.b.disabled = sansBase;
    form.elements.b.title = sansBase ? L.t.base100_non : "";
    const box = $(".at-types");
    box.textContent = "";
    const rs = raisons(S, D);
    const parRaison = new Map();
    for (const t of TYPES) {
      box.appendChild(tuile("t", t, L.court_types[t], t === S.t, { icone: t, off: rs[t], titre: rs[t] ? `${L.types[t]} : ${rs[t]}` : L.types[t] }));
      if (rs[t]) parRaison.set(rs[t], [...(parRaison.get(rs[t]) || []), L.court_types[t]]);
    }
    const ex = $("#at-raisons");
    ex.textContent = "";
    // Sur téléphone, documents et formes défilent : le choix courant est ramené en vue (sans faire défiler la page).
    for (const rang of form.querySelectorAll(".at-docs, .at-types")) {
      const on = rang.querySelector(".is-on");
      if (on && rang.scrollWidth > rang.clientWidth) rang.scrollLeft = on.offsetLeft - rang.offsetLeft - 8;
    }
    for (const [r, ts] of parRaison) {
      const p = document.createElement("p");
      const b = document.createElement("strong");
      b.textContent = ts.join(", ") + " : ";
      p.append(b, document.createTextNode(r));
      ex.appendChild(p);
    }
  }
  function lireForm() {
    const f = form.elements;
    const coches = (nom) => [...form.querySelectorAll(`input[name="${nom}"]:checked`)].map((c) => c.value);
    let e = coches("e");
    if (e.includes("*")) e = S.e[0] === "*" && e.length > 1 ? e.filter((x) => x !== "*") : ["*"];
    const t = (form.querySelector('input[name="t"]:checked') || {}).value || S.t;
    return { doc: f.doc.value, u: f.u.value, m: f.m.value, n: coches("n").join(","), e: e.join(","), t,
             a0: f.a0.value, a1: f.a1.value, z: f.z.checked ? "" : "0", b: f.b.value, titre: f.titre.value,
             st: f.st.value, an: f.an.value, fmt: f.fmt.value };
  }
  // Après un changement : si le type choisi devient impossible, on prend le premier type possible.
  function corriger(D) {
    const rs = raisons(S, D);
    if (rs[S.t]) S.t = TYPES.find((t) => !rs[t]) || S.t;
  }
  async function appliquer(r, redessiner) {
    const D = await dico(r.doc);
    S = valider(r, D);
    corriger(D);
    if (S.b && (EMPILE.has(S.t) || UNE_ANNEE.has(S.t))) S.b = null;
    history.replaceState(null, "", versUrl(S));
    if (redessiner) remplir(D); else types(D);
    selection(D);
    await rendre();
  }

  form.addEventListener("change", (ev) => {
    const r = lireForm();
    const nouveauDoc = ev.target.name === "doc";
    if (nouveauDoc) Object.assign(r, { u: "", m: "", n: "", e: "", t: "", a0: "", a1: "", b: "" });
    appliquer(r, nouveauDoc || ev.target.name === "u").catch(erreur);
  });
  let attente;
  form.addEventListener("input", (ev) => {
    if (!["titre", "st", "an"].includes(ev.target.name)) {
      if (ev.target.classList.contains("at-filtre")) filtrer(ev.target);
      return;
    }
    clearTimeout(attente);
    attente = setTimeout(() => appliquer(lireForm(), false).catch(erreur), 300);
  });
  function filtrer(inp) {
    const q = inp.value.trim().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    for (const lab of form.querySelectorAll(`.at-choix[data-nom="${inp.dataset.pour}"] label`)) {
      const t = lab.textContent.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
      lab.hidden = q && !t.includes(q) && !lab.querySelector("input").checked;
    }
  }
  root.querySelector(".at-actions").addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-act]");
    if (b) action(b.dataset.act, b).catch(erreur);
  });
  if (navigator.share) root.querySelector('[data-act="partager"]').hidden = false;
  let largeur = 0;
  window.addEventListener("resize", () => {
    const w = $("#at-plot").clientWidth;
    if (S && Math.abs(w - largeur) > 20) { largeur = w; rendre().catch(erreur); }
  });
  function erreur(e) {
    console.error(e);
    $("#at-plot").textContent = L.t.erreur;
  }

  async function demarrer() {
    root.hidden = false;
    $("#at-plot").textContent = L.t.charge;
    M = await json("/data/manifest.json");
    const r = brut();
    if (!DOCS.includes(r.doc) || !M.documents[r.doc]) r.doc = DOCS.find((k) => M.documents[k]);
    await appliquer(r, true);
    largeur = $("#at-plot").clientWidth;
  }
  if (window.Plot) demarrer().catch(erreur);
  else window.addEventListener("load", () => demarrer().catch(erreur));
})();

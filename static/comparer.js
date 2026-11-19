// Comparateur : tri, filtres, épingles et teinte appliqués à l'instant, avec la même logique que api/comparer.py.
// L'état vit dans l'adresse (lien partageable) ; sans JavaScript, en-têtes et formulaires font le même travail côté serveur.
(function () {
  const table = document.querySelector(".k-table");
  if (!table) return;
  const lang = table.dataset.lang;
  const body = table.tBodies[0];
  const rows = [...body.rows];
  const url = new URL(window.location.href);
  const P = url.searchParams;
  const nf1 = new Intl.NumberFormat(lang, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const nf0 = new Intl.NumberFormat(lang, { maximumFractionDigits: 0 });
  const unite = table.dataset.unite;
  const fmt = (v) => unite === "EUR_HAB" ? nf0.format(v) : nf1.format(unite === "EUR" ? v / 1e6 : unite === "MIO_EUR" ? v / 1e3 : v);
  const fmtD = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + nf1.format(Math.abs(v));
  const num = (s) => { if (!s) return null; const v = Number(String(s).replace(/[\s ]/g, "").replace(",", ".")); return Number.isFinite(v) ? v : null; };
  const cell = (tr, k) => tr.querySelector(`td[data-k="${CSS.escape(k)}"]`);
  const val = (tr, k) => { const c = cell(tr, k); return c && c.dataset.v !== undefined ? Number(c.dataset.v) : null; };

  function sync() {
    // Adresse, lien CSV et liens d'en-tête suivent l'état courant.
    window.history.replaceState(null, "", url.pathname + "?" + P.toString());
    const csv = document.querySelector("[data-csv]");
    if (csv) csv.href = url.pathname + ".csv?" + P.toString();
    document.querySelectorAll("form input[type=hidden]").forEach((h) => {
      if (["tri", "sens", "q", "sel", "vue", "teinte", "groupe"].includes(h.name) || /^(min|max)_/.test(h.name)) {
        if (P.has(h.name)) h.value = P.get(h.name); else h.remove();
      }
    });
  }

  function apply() {
    const q = (P.get("q") || "").toLocaleLowerCase();
    const groupe = P.get("groupe") || "";
    const sel = new Set((P.get("sel") || "").split(",").filter(Boolean));
    const vue = P.get("vue") === "sel";
    const bornes = [];
    for (const [k, v] of P) {
      const m = k.match(/^(min|max)_(.+)$/);
      if (m && num(v) !== null) bornes.push([m[1], m[2], num(v)]);
    }
    const tri = P.get("tri") || table.querySelector("th[aria-sort] [data-tri]")?.dataset.tri || "nom";
    const desc = (P.get("sens") || "desc") === "desc";
    const visibles = rows.filter((tr) => {
      if (vue && !sel.has(tr.dataset.key)) return false;
      if (q && !tr.dataset.nom.toLocaleLowerCase().includes(q)) return false;
      if (groupe && tr.dataset.groupe !== groupe) return false;
      return bornes.every(([op, k, b]) => { const v = val(tr, k); return v !== null && (op === "min" ? v >= b : v <= b); });
    });
    const key = (tr) => (tri === "nom" ? tr.dataset.nom : val(tr, tri));
    visibles.sort((a, b) => {
      const x = key(a), y = key(b);
      if (x === null && y === null) return 0;
      if (x === null) return 1;
      if (y === null) return -1;
      const c = tri === "nom" ? String(x).localeCompare(String(y), lang) : x - y;
      return desc ? -c : c;
    });
    rows.forEach((tr) => { tr.hidden = true; tr.classList.toggle("is-pin", sel.has(tr.dataset.key)); tr.querySelector("[data-pin]").checked = sel.has(tr.dataset.key); });
    // Rang dans l'ordre du tri ; les lignes épinglées remontent en tête et gardent leur rang.
    visibles.forEach((tr, i) => { tr.hidden = false; tr.querySelector(".k-rang").textContent = i + 1; });
    visibles.filter((tr) => sel.has(tr.dataset.key)).concat(visibles.filter((tr) => !sel.has(tr.dataset.key))).forEach((tr) => body.appendChild(tr));
    rows.filter((tr) => tr.hidden).forEach((tr) => body.appendChild(tr));
    // En-têtes : sens du tri.
    table.querySelectorAll("thead [data-tri]").forEach((a) => {
      const th = a.closest("th");
      if (a.dataset.tri === tri) th.setAttribute("aria-sort", desc ? "descending" : "ascending"); else th.removeAttribute("aria-sort");
    });
    // Statistiques sur les lignes affichées (calcul du site).
    table.querySelectorAll("tfoot tr[data-stat]").forEach((tr) => {
      tr.querySelectorAll("td[data-k]").forEach((td) => {
        const xs = visibles.map((r) => val(r, td.dataset.k)).filter((v) => v !== null).sort((a, b) => a - b);
        if (!xs.length) { td.textContent = "—"; return; }
        const n = xs.length;
        const v = { med: n % 2 ? xs[(n - 1) / 2] : (xs[n / 2 - 1] + xs[n / 2]) / 2, min: xs[0], max: xs[n - 1] }[tr.dataset.stat];
        td.textContent = td.dataset.k.startsWith("d:") ? fmtD(v) : fmt(v);
      });
    });
    // Teinte : intensité relative au maximum de la colonne parmi les lignes affichées.
    table.classList.toggle("is-teinte", P.get("teinte") === "1");
    table.querySelectorAll("thead [data-tri]").forEach((a) => {
      const k = a.dataset.tri;
      if (k === "nom") return;
      const max = Math.max(0, ...visibles.map((r) => Math.abs(val(r, k) ?? 0)));
      rows.forEach((r) => { const c = cell(r, k); const v = val(r, k); if (c && v !== null) c.style.setProperty("--k", max ? (Math.abs(v) / max).toFixed(3) : 0); });
    });
    document.querySelectorAll("[data-nvis]").forEach((n) => (n.textContent = visibles.length));
    document.querySelectorAll("[data-nsel]").forEach((n) => (n.textContent = sel.size));
    const vide = document.querySelector(".k-vide");
    if (vide) vide.hidden = visibles.length > 0;
    sync();
  }

  function set(k, v) { if (v === null || v === "" || v === undefined) P.delete(k); else P.set(k, v); apply(); }

  // Tri : clic sur un en-tête ; second clic inverse le sens.
  table.querySelectorAll("thead [data-tri]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    const k = a.dataset.tri;
    const cur = P.get("tri") || table.querySelector("th[aria-sort] [data-tri]")?.dataset.tri;
    const sens = cur === k ? ((P.get("sens") || "desc") === "desc" ? "asc" : "desc") : (k === "nom" ? "asc" : "desc");
    P.set("tri", k); P.set("sens", sens); apply();
  }));

  // Filtres : nom, fonction parente, bornes min/max, vue épinglée, teinte.
  const outils = document.querySelector("[data-filtres]");
  outils.addEventListener("submit", (e) => e.preventDefault());
  let t;
  outils.querySelector("input[name=q]").addEventListener("input", (e) => { clearTimeout(t); t = setTimeout(() => set("q", e.target.value.trim()), 80); });
  const g = outils.querySelector("select[name=groupe]");
  if (g) g.addEventListener("change", () => set("groupe", g.value));
  outils.querySelector("[data-vue]").addEventListener("change", (e) => set("vue", e.target.checked ? "sel" : null));
  outils.querySelector("[data-teinte]").addEventListener("change", (e) => set("teinte", e.target.checked ? "1" : null));
  document.querySelector("[data-bornes]").addEventListener("submit", (e) => e.preventDefault());
  table.querySelectorAll("[data-min], [data-max]").forEach((inp) => inp.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => set(inp.name, num(inp.value) === null ? null : inp.value.trim()), 150);
  }));

  // Épingles.
  body.addEventListener("change", (e) => {
    if (!e.target.matches("[data-pin]")) return;
    const sel = new Set((P.get("sel") || "").split(",").filter(Boolean));
    const k = e.target.closest("tr").dataset.key;
    if (e.target.checked) sel.add(k); else sel.delete(k);
    set("sel", [...sel].join(","));
  });

  // Réglages qui changent les données : rechargés par le serveur.
  const reg = document.querySelector("form[data-auto]");
  reg.querySelectorAll("select").forEach((s) => s.addEventListener("change", () => { document.body.classList.add("is-loading"); reg.requestSubmit(); }));
  const hidden = reg.querySelector("[data-cols]");
  const boxes = [...reg.querySelectorAll("[data-col]")];
  const limite = () => { const n = boxes.filter((b) => b.checked).length; boxes.forEach((b) => (b.disabled = !b.checked && n >= 8)); };
  const nb = reg.querySelector("[data-nb-cols]");
  const appliquer = reg.querySelector("[data-appliquer]");
  const choix = () => boxes.filter((x) => x.checked).map((x) => x.value).join(",");
  const depart = choix();
  const suivre = () => { nb.textContent = boxes.filter((b) => b.checked).length; appliquer.disabled = choix() === depart; };
  boxes.forEach((b) => b.addEventListener("change", () => { hidden.value = choix(); limite(); suivre(); }));
  limite();
  suivre();
  // Onglets des familles de colonnes (collectivités), et détail dépliable de chaque rubrique.
  const onglets = [...reg.querySelectorAll("[data-onglet]")];
  const montrerOnglet = (cle) => {
    onglets.forEach((o) => o.setAttribute("aria-selected", String(o.dataset.onglet === cle)));
    reg.querySelectorAll("[data-panneau]").forEach((p) => p.toggleAttribute("data-cache", p.dataset.panneau !== cle));
  };
  onglets.forEach((o) => o.addEventListener("click", () => montrerOnglet(o.dataset.onglet)));
  // On ouvre sur la famille de la première colonne cochée.
  const premiere = reg.querySelector("[data-panneau] [data-col]:checked");
  if (premiere) montrerOnglet(premiere.closest("[data-panneau]").dataset.panneau);
  reg.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-dep]");
    if (!b) return;
    const ouvert = b.getAttribute("aria-expanded") !== "true";
    b.setAttribute("aria-expanded", String(ouvert));
    b.closest("[data-n]").querySelector(":scope > .k-sous").hidden = !ouvert;
  });
  const compterOnglets = () => onglets.forEach((o) => {
    const n = reg.querySelectorAll(`[data-panneau="${o.dataset.onglet}"] [data-col]:checked`).length;
    o.querySelector("[data-on-n]").textContent = n || "";
  });
  boxes.forEach((b) => b.addEventListener("change", compterOnglets));
  // Recherche dans les colonnes (sans accents) ; une famille sans résultat est masquée.
  const qCols = reg.querySelector("[data-cols-q]");
  const plat = (s) => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  if (qCols && onglets.length) qCols.addEventListener("input", () => {
    const q = plat(qCols.value.trim());
    const garde = (n) => {
      const soi = plat(n.querySelector(":scope > .k-ligne").textContent).includes(q);
      const sous = [...n.querySelectorAll(":scope > .k-sous > [data-n]")].map(garde).some(Boolean);
      n.hidden = q && !soi && !sous;
      const s = n.querySelector(":scope > .k-sous");
      const b = n.querySelector(":scope > .k-ligne [data-dep]");
      if (s) s.hidden = q ? !sous : b.getAttribute("aria-expanded") !== "true";
      return soi || sous;
    };
    reg.querySelectorAll("[data-panneau]").forEach((p) => {
      const ok = [...p.querySelectorAll(":scope > [data-n], :scope .k-grille > [data-n]")].map(garde).some(Boolean);
      p.toggleAttribute("data-cache", q ? !ok : p.dataset.panneau !== (onglets.find((o) => o.getAttribute("aria-selected") === "true") || onglets[0]).dataset.onglet);
    });
    reg.querySelectorAll(".k-autre").forEach((d) => { if (q) d.open = true; });
    reg.querySelector(".k-onglets").hidden = !!q;
  });
  else if (qCols) qCols.addEventListener("input", () => {
    const q = plat(qCols.value.trim());
    reg.querySelectorAll("[data-groupe-cols]").forEach((fs) => {
      let n = 0;
      fs.querySelectorAll(".k-check").forEach((l) => { const ok = !q || plat(l.textContent).includes(q); l.hidden = !ok; n += ok; });
      fs.hidden = !n;
    });
  });
  if (qCols) qCols.addEventListener("keydown", (ev) => { if (ev.key === "Enter") ev.preventDefault(); });
  reg.addEventListener("submit", () => {
    if (!hidden.value) hidden.remove();
    // Les champs d'état sont ceux de l'adresse courante (tri, filtres, épingles mis à jour sans rechargement).
    reg.querySelectorAll("input[type=hidden]:not([data-cols])").forEach((h) => h.remove());
    for (const [k, v] of P) if (!["niveau", "unite", "annee", "ref", "cols"].includes(k)) {
      const h = document.createElement("input"); h.type = "hidden"; h.name = k; h.value = v; reg.appendChild(h);
    }
  });

  // Copier le lien.
  const copy = document.querySelector("[data-copy]");
  copy.hidden = false;
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(window.location.href); copy.textContent = copy.dataset.done; }
    catch (e) { window.prompt("", window.location.href); }
  });

  apply();
})();

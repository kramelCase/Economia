// Graphiques : dessinés à partir du HTML rendu par le serveur (légendes, tableaux, listes), qui reste la
// version lisible sans JavaScript. Aucun chiffre n'est calculé ni formaté ici : tout vient de la page.
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const tip = document.createElement("div");
  tip.className = "ctip";
  tip.hidden = true;
  document.body.appendChild(tip);

  function el(name, attrs, parent) {
    const n = document.createElementNS(NS, name);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  // Infobulle : la valeur d'abord, le libellé ensuite (textContent seulement).
  function showTip(x, y, rows) {
    tip.textContent = "";
    rows.forEach((r) => {
      const line = document.createElement("div");
      line.className = "ctip-row";
      if (r.slot !== undefined) {
        const key = document.createElement("span");
        key.className = "ctip-key";
        key.style.background = `var(--s${r.slot})`;
        line.appendChild(key);
      }
      const v = document.createElement("strong");
      v.textContent = r.value;
      line.appendChild(v);
      if (r.label) {
        const l = document.createElement("span");
        l.textContent = r.label;
        line.appendChild(l);
      }
      tip.appendChild(line);
    });
    tip.hidden = false;
    const w = tip.offsetWidth;
    const vw = document.documentElement.clientWidth;
    tip.style.left = Math.max(8, Math.min(x + 12, window.scrollX + vw - w - 8)) + "px";
    tip.style.top = (y + 14) + "px";
  }
  function hideTip() { tip.hidden = true; }

  // --- Anneau (camembert) : les segments viennent des lignes de légende li[data-v][data-slot] ---
  function arc(cx, cy, r0, r1, a0, a1) {
    const large = a1 - a0 > Math.PI ? 1 : 0;
    const p = (r, a) => [cx + r * Math.sin(a), cy - r * Math.cos(a)];
    const [x0, y0] = p(r1, a0), [x1, y1] = p(r1, a1), [x2, y2] = p(r0, a1), [x3, y3] = p(r0, a0);
    return `M${x0} ${y0}A${r1} ${r1} 0 ${large} 1 ${x1} ${y1}L${x2} ${y2}A${r0} ${r0} 0 ${large} 0 ${x3} ${y3}Z`;
  }

  function donut(fig) {
    const box = fig.querySelector(".donut");
    const rows = [...fig.querySelectorAll(".legend > li[data-v]")];
    const vals = rows.map((li) => Math.max(0, parseFloat(li.dataset.v) || 0));
    const sum = vals.reduce((a, b) => a + b, 0);
    if (!box || !sum) return;
    const svg = el("svg", { viewBox: "0 0 200 200", role: "img", "aria-hidden": "true" });
    let a = 0;
    const paths = rows.map((li, i) => {
      const da = (vals[i] / sum) * Math.PI * 2;
      const d = da >= Math.PI * 2 - 1e-6 ? arc(100, 100, 60, 96, 0, Math.PI * 2 - 1e-4) : arc(100, 100, 60, 96, a, a + da);
      const path = el("path", { d, class: "seg", style: `fill: var(--s${li.dataset.slot})` }, svg);
      a += da;
      const link = li.querySelector("a.lg-label");
      const label = (li.querySelector(".lg-name") || li).textContent.trim();
      const value = (li.querySelector(".lg-share") || {}).textContent || "";
      const extra = (li.querySelector(".lg-amount") || {}).textContent || "";
      const on = () => { fig.classList.add("is-hot"); li.classList.add("hot"); path.classList.add("hot"); };
      const off = () => { fig.classList.remove("is-hot"); li.classList.remove("hot"); path.classList.remove("hot"); hideTip(); };
      path.addEventListener("pointermove", (e) => { on(); showTip(e.pageX, e.pageY, [{ value: value.trim(), label: `${label} · ${extra.trim()}`, slot: li.dataset.slot }]); });
      path.addEventListener("pointerleave", off);
      if (link) path.addEventListener("click", () => { window.location.href = link.href; });
      else path.style.cursor = "default";
      li.addEventListener("pointerenter", on);
      li.addEventListener("pointerleave", off);
      li.addEventListener("focusin", on);
      li.addEventListener("focusout", off);
      return path;
    });
    box.prepend(svg);
    return paths;
  }

  // --- Courbe : données JSON dans la figure, tableau jumeau rendu par le serveur ---
  function line(fig) {
    const data = JSON.parse(fig.querySelector("script[type='application/json']").textContent);
    const box = fig.querySelector(".plot");
    const xs = data.x;
    if (!box || xs.length < 2) return;
    function draw() {
      box.textContent = "";
      const W = Math.max(260, box.clientWidth), H = W < 480 ? 200 : 240;
      const m = { t: 12, r: 12, b: 26, l: 48 };
      const all = data.series.flatMap((s) => s.points.filter((p) => p).map((p) => p.v));
      let lo = Math.min(...all), hi = Math.max(...all);
      const pad = (hi - lo) * 0.12 || Math.abs(hi) * 0.1 || 1;
      lo = data.zero && lo >= 0 ? 0 : lo - pad;
      hi += pad;
      // Barres : une bande par année ; courbe et aire : un point par année, du bord gauche au bord droit.
      const bars = data.forme === "barres";
      const band = (W - m.l - m.r) / (bars ? xs.length : xs.length - 1);
      const X = (i) => m.l + band * (bars ? i + 0.5 : i);
      // Graduations : montants en euros ramenés au milliard ou au million (data.mult = euros par unité).
      const lang = document.documentElement.lang;
      const big = data.mult ? Math.max(Math.abs(hi), Math.abs(lo)) * data.mult : 0;
      const [div, suf] = big >= 1e9 ? [1e9, data.suf[0]] : big >= 1e6 ? [1e6, data.suf[1]] : [1, ""];
      const tick = (v) => {
        if (data.mult) {
          const x = (v * data.mult) / div;
          return x.toLocaleString(lang, { maximumFractionDigits: (hi - lo) * data.mult / div < 10 ? 1 : 0 }) + (suf ? " " + suf : " €");
        }
        return (data.tick || "{v}").replace("{v}", v.toLocaleString(lang, { maximumFractionDigits: Math.abs(hi - lo) < 10 ? 1 : 0 }));
      };
      const Y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
      const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, "aria-hidden": "true" }, box);
      for (let k = 0; k <= 3; k++) {
        const v = lo + ((hi - lo) * k) / 3;
        el("line", { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), class: k === 0 ? "axis" : "grid" }, svg);
        const t = el("text", { x: m.l - 6, y: Y(v) + 4, class: "tick", "text-anchor": "end" }, svg);
        t.textContent = tick(v);
      }
      const step = Math.ceil(xs.length / (W < 480 ? 5 : 9));
      xs.forEach((x, i) => {
        const last = xs.length - 1;
        if (i !== last && (i % step || last - i < step * 0.6)) return;
        const t = el("text", { x: X(i), y: H - 6, class: "tick", "text-anchor": "middle" }, svg);
        t.textContent = x;
      });
      const base = Y(Math.max(lo, Math.min(0, hi)));
      if (lo < 0 && hi > 0) el("line", { x1: m.l, x2: W - m.r, y1: Y(0), y2: Y(0), class: "axis" }, svg);
      (data.reperes || []).forEach((r) => {
        const i = xs.indexOf(r.an);
        if (i < 0) return;
        const x = bars ? m.l + band * (i + r.frac) : X(i) + band * r.frac;
        if (x > W - m.r) return;
        el("line", { x1: x, x2: x, y1: m.t, y2: H - m.b, class: "repere" }, svg);
        const t = el("text", { x: x + 3, y: m.t + 9, class: "tick repere-t" }, svg);
        t.textContent = r.t;
      });
      data.series.forEach((s, k) => {
        if (bars) {
          const gw = band * 0.72, bw = gw / data.series.length;
          s.points.forEach((p, i) => {
            if (!p) return;
            const y = Y(p.v);
            el("rect", { x: X(i) - gw / 2 + k * bw + 0.5, y: Math.min(y, base), width: Math.max(1, bw - 1),
              height: Math.max(1, Math.abs(base - y)), class: "col" + (p.prov ? " is-prov" : ""),
              style: `fill: var(--s${s.slot}); stroke: var(--s${s.slot})` }, svg);
          });
          return;
        }
        let d = "";
        s.points.forEach((p, i) => { if (p) d += `${d && s.points[i - 1] ? "L" : "M"}${X(i)} ${Y(p.v)}`; });
        if (data.forme === "aires") {
          const idx = s.points.map((p, i) => (p ? i : -1)).filter((i) => i >= 0);
          if (idx.length) el("path", { d: `${d}L${X(idx[idx.length - 1])} ${base}L${X(idx[0])} ${base}Z`, class: "area",
            style: `fill: var(--s${s.slot})` }, svg);
        }
        el("path", { d, class: "serie", style: `stroke: var(--s${s.slot})` }, svg);
        // Valeur provisoire : point creux ; dernière valeur : point plein (sauf si provisoire).
        s.points.forEach((p, i) => {
          if (p && p.prov) el("circle", { cx: X(i), cy: Y(p.v), r: 3.5, class: "dot is-prov", style: `stroke: var(--s${s.slot})` }, svg);
        });
        const last = s.points.length - 1;
        if (s.points[last] && !s.points[last].prov) el("circle", { cx: X(last), cy: Y(s.points[last].v), r: 4, class: "dot", style: `fill: var(--s${s.slot})` }, svg);
      });
      const hair = el("line", { y1: m.t, y2: H - m.b, class: "hair", visibility: "hidden" }, svg);
      const dots = data.series.map((s) => el("circle", { r: 4, class: "dot", visibility: "hidden", style: `fill: var(--s${s.slot})` }, svg));
      let cur = -1;
      const hit = el("rect", { x: m.l, y: 0, width: W - m.l - m.r, height: H, fill: "transparent" }, svg);
      hit.addEventListener("pointermove", (e) => {
        const r = svg.getBoundingClientRect();
        const px = ((e.clientX - r.left) / r.width) * W;
        cur = Math.max(0, Math.min(xs.length - 1, bars ? Math.floor((px - m.l) / band) : Math.round((px - m.l) / band)));
        hair.setAttribute("x1", X(cur)); hair.setAttribute("x2", X(cur)); hair.setAttribute("visibility", "visible");
        const rows = [{ value: String(xs[cur]) }];
        data.series.forEach((s, k) => {
          const p = s.points[cur];
          if (!p) { dots[k].setAttribute("visibility", "hidden"); return; }
          dots[k].setAttribute("cx", X(cur)); dots[k].setAttribute("cy", Y(p.v)); dots[k].setAttribute("visibility", "visible");
          rows.push({ value: p.f, label: s.name + (p.prov ? ` (${data.prov})` : ""), slot: s.slot });
        });
        showTip(e.pageX, e.pageY, rows);
      });
      hit.addEventListener("pointerleave", () => { hair.setAttribute("visibility", "hidden"); dots.forEach((d) => d.setAttribute("visibility", "hidden")); cur = -1; hideTip(); });
      hit.addEventListener("click", () => { const p = cur >= 0 && data.series[0].points[cur]; if (p && p.href) window.location.href = p.href; });
      hit.style.cursor = "pointer";
    }
    draw();
    let w = box.clientWidth;
    new ResizeObserver(() => { if (Math.abs(box.clientWidth - w) > 20) { w = box.clientWidth; draw(); } }).observe(box);
  }

  // --- Classement : tri et recherche sur une liste ol.rank > li[data-v][data-name] ---
  function rank(wrap) {
    const list = wrap.querySelector("ol.rank");
    const items = [...list.children];
    const search = wrap.querySelector("input[type=search]");
    const count = wrap.querySelector(".rank-count");
    wrap.querySelectorAll("button[data-sort]").forEach((b) => b.addEventListener("click", () => {
      wrap.querySelectorAll("button[data-sort]").forEach((o) => o.setAttribute("aria-pressed", o === b));
      const k = b.dataset.sort;
      const cmp = k === "name" ? (x, y) => x.dataset.name.localeCompare(y.dataset.name, document.documentElement.lang)
        : (x, y) => (k === "asc" ? 1 : -1) * (parseFloat(x.dataset.v) - parseFloat(y.dataset.v));
      items.sort(cmp).forEach((li) => list.appendChild(li));
    }));
    if (search) search.addEventListener("input", () => {
      const s = search.value.trim().toLocaleLowerCase();
      let n = 0;
      items.forEach((li) => { const ok = !s || li.dataset.name.toLocaleLowerCase().includes(s); li.hidden = !ok; n += ok; });
      if (count) count.textContent = n;
    });
  }

  // --- Tableaux triables : th[data-sort] ; td[data-v] pour les nombres ---
  function sortable(table) {
    const ths = [...table.tHead.rows[0].cells];
    ths.forEach((th, col) => {
      if (!("sort" in th.dataset)) return;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "th-sort";
      while (th.firstChild) b.appendChild(th.firstChild);
      th.appendChild(b);
      b.addEventListener("click", () => {
        const dir = th.getAttribute("aria-sort") === "descending" ? 1 : -1;
        ths.forEach((o) => o.removeAttribute("aria-sort"));
        th.setAttribute("aria-sort", dir === 1 ? "ascending" : "descending");
        const body = table.tBodies[0];
        const key = (tr) => {
          const c = tr.cells[col];
          return c && c.dataset.v !== undefined ? parseFloat(c.dataset.v) : (c ? c.textContent.trim() : "");
        };
        [...body.rows].sort((x, y) => {
          const a = key(x), b2 = key(y);
          return dir * (typeof a === "number" ? a - b2 : String(a).localeCompare(String(b2), document.documentElement.lang));
        }).forEach((tr) => body.appendChild(tr));
      });
    });
  }

  // Recherche dans un tableau : input[data-filter="#id-du-tableau"]
  document.querySelectorAll("input[data-filter]").forEach((inp) => {
    const table = document.querySelector(inp.dataset.filter);
    const count = document.querySelector(inp.dataset.count || "#none");
    inp.addEventListener("input", () => {
      const s = inp.value.trim().toLocaleLowerCase();
      let n = 0;
      [...table.tBodies[0].rows].forEach((tr) => { const ok = !s || tr.textContent.toLocaleLowerCase().includes(s); tr.hidden = !ok; n += ok; });
      if (count) count.textContent = n;
    });
  });

  // Filtres : appliqués dès qu'on change une valeur ; l'affichage précédent reste visible, estompé.
  document.querySelectorAll("form.filters").forEach((form) => {
    form.querySelectorAll("select").forEach((s) => s.addEventListener("change", () => {
      document.body.classList.add("is-loading");
      form.submit();
    }));
    const btn = form.querySelector("button[type=submit]");
    if (btn) btn.classList.add("js-hide");
  });

  document.querySelectorAll(".donut-chart").forEach(donut);
  document.querySelectorAll(".line-chart").forEach(line);
  window.CPCharts = { line };  // pour les contenus remplacés sans rechargement (static/carte.js)
  document.querySelectorAll(".rank-wrap").forEach(rank);
  document.querySelectorAll("table.sortable").forEach(sortable);
  window.addEventListener("pageshow", () => document.body.classList.remove("is-loading"));
})();

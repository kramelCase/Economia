// Palette de commandes (Ctrl+K, « / », bouton « Rechercher ») : aller à un objet, avec son chiffre, ou lancer une
// action sur lui (comparer, tracer la série). Avant toute saisie : les objets récents et les pages du site.
// Sans JavaScript, le bouton mène à la page de recherche. Les récents restent dans ce navigateur seulement.
(function () {
  const dlg = document.getElementById("cmd");
  if (!dlg || typeof dlg.showModal !== "function") return;
  const input = document.getElementById("cmd-q");
  const list = document.getElementById("cmd-list");
  const T = JSON.parse(document.getElementById("cmd-data").textContent);
  const KEY = "cp:recents";
  let items = [], cur = 0, act = -1, seq = 0, timer = null, words = [];

  // Menu repliable sur téléphone.
  const tog = document.querySelector(".nav-tog");
  const nav = document.getElementById("nav");
  if (tog && nav) {
    document.documentElement.classList.add("js-menu");
    tog.hidden = false;
    tog.addEventListener("click", () => {
      const open = !nav.classList.contains("is-open");
      nav.classList.toggle("is-open", open);
      tog.setAttribute("aria-expanded", String(open));
    });
  }

  const recents = () => { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } };
  function remember(it) {
    try {
      const r = recents().filter((x) => x.href !== it.href);
      r.unshift({ g: it.g, t: it.t, href: it.href, fig: it.fig || null, an: it.an || null, actions: it.actions || [] });
      localStorage.setItem(KEY, JSON.stringify(r.slice(0, 6)));
    } catch (e) { /* stockage indisponible : pas de récents */ }
  }

  const fold = (s) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function highlight(node, text) {
    const f = fold(text);
    const marks = words.map((w) => [f.indexOf(w), w.length]).filter(([i]) => i >= 0).sort((a, b) => a[0] - b[0]);
    let pos = 0;
    marks.forEach(([i, n]) => { if (i < pos) return; node.append(text.slice(pos, i), el("mark", null, text.slice(i, i + n))); pos = i + n; });
    node.append(text.slice(pos));
  }

  function render(data, vide) {
    items = data; cur = 0; act = -1; list.replaceChildren();
    if (!data.length) { list.append(el("li", "cmd-vide", vide || T.vide)); input.removeAttribute("aria-activedescendant"); return; }
    let g = null;
    data.forEach((d, i) => {
      const grp = d.sect || d.g;
      if (grp !== g) { g = grp; const h = el("li", "cmd-grp", g); h.setAttribute("role", "presentation"); list.append(h); }
      const li = el("li"); li.id = "cmd-o" + i; li.setAttribute("role", "option");
      const t = el("span", "cmd-t"); highlight(t, d.t); li.append(t);
      if (d.fig || d.gap) { const f = el("span", "cmd-f2" + (d.gap ? " is-gap" : ""), d.fig || d.gap); if (d.an && d.fig) f.append(el("small", null, String(d.an))); li.append(f); }
      else if (d.sect && d.g) li.append(el("span", "cmd-f2", d.g));
      if (d.actions && d.actions.length) {
        const a = el("span", "cmd-acts");
        d.actions.forEach((x, k) => { const b = el("a", null, x.t); b.href = x.href; b.tabIndex = -1; b.dataset.k = k; a.append(b); });
        li.append(a);
      }
      li.addEventListener("mousemove", () => { if (cur !== i) { cur = i; act = -1; paint(); } });
      li.addEventListener("click", (e) => {
        const k = e.target.closest("[data-k]");
        e.preventDefault();
        open(i, k ? Number(k.dataset.k) : -1);
      });
      list.append(li);
    });
    paint();
  }

  function paint() {
    list.querySelectorAll('[role="option"]').forEach((o, i) => {
      o.setAttribute("aria-selected", i === cur ? "true" : "false");
      o.querySelectorAll("[data-k]").forEach((b) => b.classList.toggle("is-on", i === cur && Number(b.dataset.k) === act));
    });
    const o = document.getElementById("cmd-o" + cur);
    if (o) { input.setAttribute("aria-activedescendant", o.id); o.scrollIntoView({ block: "nearest" }); }
  }

  function open(i, k) {
    const it = items[i];
    if (!it) return;
    remember(it);
    window.location.href = k >= 0 && it.actions ? it.actions[k].href : it.href;
  }

  function accueil() {
    words = [];
    const r = recents().map((x) => ({ ...x, sect: T.recents }));
    render(r.concat(T.pages.map((p) => ({ ...p, sect: T.aller }))));
  }

  async function chercher(v) {
    words = fold(v).split(/\s+/).filter(Boolean);
    const mine = ++seq;
    let data = [];
    try { data = await (await fetch(input.dataset.src + "?q=" + encodeURIComponent(v))).json(); } catch (e) { /* hors ligne */ }
    if (mine !== seq) return;
    const pages = T.pages.filter((p) => words.every((w) => fold(p.t + " " + p.g).includes(w))).map((p) => ({ ...p, sect: T.aller }));
    render(data.concat(pages));
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const v = input.value.trim();
    if (!v) { seq++; accueil(); return; }
    timer = setTimeout(() => chercher(v), 100);
  });

  input.addEventListener("keydown", (e) => {
    const n = items.length;
    const nact = n ? (items[cur].actions || []).length : 0;
    if (e.key === "ArrowDown" && n) { e.preventDefault(); cur = (cur + 1) % n; act = -1; paint(); }
    else if (e.key === "ArrowUp" && n) { e.preventDefault(); cur = (cur - 1 + n) % n; act = -1; paint(); }
    else if (e.key === "ArrowRight" && nact && input.selectionStart === input.value.length) { e.preventDefault(); act = Math.min(act + 1, nact - 1); paint(); }
    else if (e.key === "ArrowLeft" && act >= 0) { e.preventDefault(); act -= 1; paint(); }
    else if (e.key === "Enter" && n && items[cur]) { e.preventDefault(); open(cur, act); }
    // Entrée sans résultat : le formulaire mène à la page de recherche.
  });

  function show(e) {
    if (e) e.preventDefault();
    if (dlg.open) return;
    dlg.showModal();
    input.value = "";
    accueil();
    input.focus();
  }
  document.querySelectorAll("[data-cmd-open]").forEach((b) => b.addEventListener("click", show));
  dlg.querySelector("[data-cmd-close]").addEventListener("click", () => dlg.close());
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  document.addEventListener("keydown", (e) => {
    const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") show(e);
    // « / » ouvre la palette, sauf là où la page a sa propre recherche (prototype /explorer).
    else if (e.key === "/" && !typing && !document.getElementById("x-s")) show(e);
  });
})();

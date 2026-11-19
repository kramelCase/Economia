// Prototype « explorer » : la phrase se répond dès qu'on change un mot (navigation normale, fondu par
// View Transitions), et la recherche typée propose des entrées qui portent déjà leur chiffre.
// Sans JavaScript : le bouton « Répondre » soumet la phrase ; les portes du sommaire restent.
(function () {
  const form = document.querySelector(".x-phrase");
  if (form) form.querySelectorAll("select").forEach((s) => s.addEventListener("change", () => form.submit()));

  // Rubans de sujets : un bouton arrête le défilement (WCAG 2.2.2), le choix est retenu pour la visite suivante.
  const sujets = document.querySelector(".x-sujets");
  const pause = sujets && sujets.querySelector(".x-pause");
  if (pause) {
    const set = (on) => {
      sujets.classList.toggle("is-paused", on); pause.setAttribute("aria-pressed", String(on));
      pause.textContent = on ? pause.dataset.play : pause.dataset.pause;
    };
    try { set(localStorage.getItem("cp:rubans") === "pause"); } catch (e) { /* stockage indisponible */ }
    pause.addEventListener("click", () => {
      const on = !sujets.classList.contains("is-paused");
      set(on);
      try { localStorage.setItem("cp:rubans", on ? "pause" : ""); } catch (e) { /* idem */ }
    });
  }

  const input = document.getElementById("x-s");
  const list = document.getElementById("x-list");
  const hint = document.querySelector(".x-hint");
  if (!input || !list) return;
  let items = [], active = -1, timer = null, seq = 0;

  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // Met en gras les mots tapés, sans jamais injecter de HTML.
  function highlight(node, text, words) {
    const fold = (s) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
    const f = fold(text);
    const marks = [];
    words.forEach((w) => { const i = f.indexOf(w); if (i >= 0) marks.push([i, i + w.length]); });
    marks.sort((a, b) => a[0] - b[0]);
    let pos = 0;
    marks.forEach(([a, b]) => {
      if (a < pos) return;
      node.append(text.slice(pos, a), el("mark", null, text.slice(a, b)));
      pos = b;
    });
    node.append(text.slice(pos));
  }

  function close() {
    list.hidden = true; input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant");
    active = -1;
  }

  function select(i) {
    const opts = list.querySelectorAll('[role="option"]');
    opts.forEach((o, k) => o.setAttribute("aria-selected", k === i ? "true" : "false"));
    active = i;
    if (opts[i]) { input.setAttribute("aria-activedescendant", opts[i].id); opts[i].scrollIntoView({ block: "nearest" }); }
  }

  function render(data, words) {
    items = data; list.replaceChildren(); active = -1;
    if (hint) { hint.hidden = data.length > 0 || !input.value.trim(); hint.textContent = hint.dataset.empty; }
    if (!data.length) return close();
    let group = null;
    data.forEach((d, i) => {
      if (d.g !== group) { group = d.g; list.append(el("li", "x-grp", group)); list.lastChild.setAttribute("role", "presentation"); }
      const li = el("li");
      li.id = "x-o" + i; li.setAttribute("role", "option"); li.setAttribute("aria-selected", "false");
      const t = el("span", "x-t"); highlight(t, d.t, words); li.append(t);
      if (d.fig || d.gap) {
        const f = el("span", "x-f" + (d.gap ? " is-gap" : ""), d.fig || d.gap);
        if (d.an && d.fig) f.append(el("small", null, String(d.an)));
        li.append(f);
      }
      li.addEventListener("mousedown", (e) => { e.preventDefault(); go(i); });
      list.append(li);
    });
    list.hidden = false; input.setAttribute("aria-expanded", "true");
  }

  function go(i) { if (items[i]) window.location.href = items[i].href; }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const v = input.value.trim();
    if (!v) { render([], []); return; }
    timer = setTimeout(async () => {
      const mine = ++seq;
      try {
        const r = await fetch(input.dataset.src + "?q=" + encodeURIComponent(v));
        const data = await r.json();
        if (mine !== seq) return; // une frappe plus récente a déjà répondu
        const words = v.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().split(/\s+/);
        render(data, words);
      } catch (e) { close(); }
    }, 120);
  });

  input.addEventListener("keydown", (e) => {
    const n = items.length;
    if (e.key === "ArrowDown" && n) { e.preventDefault(); if (list.hidden) list.hidden = false; select((active + 1) % n); }
    else if (e.key === "ArrowUp" && n) { e.preventDefault(); select((active - 1 + n) % n); }
    else if (e.key === "Enter" && n) { e.preventDefault(); go(active >= 0 ? active : 0); } // sinon : page de résultats
    else if (e.key === "Escape") { if (!list.hidden) close(); else input.value = ""; }
  });
  input.addEventListener("blur", () => setTimeout(close, 100));
  input.addEventListener("focus", () => { if (items.length && input.value.trim()) { list.hidden = false; input.setAttribute("aria-expanded", "true"); } });

  // « / » donne la main à la recherche, sauf si l'on écrit déjà quelque part.
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); input.focus(); }
  });
})();

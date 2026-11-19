// Carte de l'accueil : zoom, périmètre, unité et année sans recharger la page.
// Sans JavaScript, chaque case et chaque réglage est un lien ou un formulaire ordinaire.
(function () {
  const sel = "#carte";
  let ctrl = null;
  let timer = null;

  function swap(next) {
    const cur = document.querySelector(sel);
    cur.replaceWith(next);
    init(next);
  }

  async function go(url, mode) {
    if (ctrl) ctrl.abort();
    ctrl = new AbortController();
    const cur = document.querySelector(sel);
    cur.classList.add("is-loading");
    let html;
    try {
      html = await (await fetch(url, { signal: ctrl.signal })).text();
    } catch (e) {
      if (e.name !== "AbortError") window.location.href = url;
      return;
    }
    const next = new DOMParser().parseFromString(html, "text/html").querySelector(sel);
    if (!next) { window.location.href = url; return; }
    if (mode === "push") history.pushState(null, "", url);
    else history.replaceState(null, "", url);
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (document.startViewTransition && !still && mode !== "quiet") document.startViewTransition(() => swap(next));
    else swap(next);
    if (mode === "push") {
      const top = document.querySelector(sel).getBoundingClientRect().top;
      if (top < 0) document.querySelector(sel).scrollIntoView({ block: "start" });
    }
  }

  function urlAnnee(form, annee) {
    const p = new URLSearchParams(new FormData(form));
    p.set("annee", annee);
    if (Number(annee) === Number(form.querySelector("input[type=range]").max)) p.delete("annee");
    return form.getAttribute("action").replace("#carte", "") + "?" + p.toString() + "#carte";
  }

  function stop(btn) {
    clearInterval(timer);
    timer = null;
    if (btn) btn.setAttribute("aria-pressed", "false");
  }

  function init(root) {
    root.querySelectorAll("a[data-carte]").forEach((a) => a.addEventListener("click", (e) => {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
      e.preventDefault();
      stop();
      go(a.href, "push");
    }));
    const form = root.querySelector(".c-temps");
    const range = form.querySelector("input[type=range]");
    const out = form.querySelector("output");
    let t;
    range.addEventListener("input", () => {
      out.textContent = range.value;
      clearTimeout(t);
      t = setTimeout(() => go(urlAnnee(form, range.value), "replace"), 120);
    });
    form.addEventListener("submit", (e) => { e.preventDefault(); go(urlAnnee(form, range.value), "replace"); });
    const btn = form.querySelector("[data-play]");
    btn.hidden = false;
    if (timer) btn.setAttribute("aria-pressed", "true");
    btn.addEventListener("click", () => {
      if (timer) { stop(btn); return; }
      let y = Number(range.value);
      if (y >= Number(range.max)) y = Number(range.min) - 1;
      btn.setAttribute("aria-pressed", "true");
      const step = () => {
        y += 1;
        if (y > Number(range.max)) { stop(document.querySelector(sel + " [data-play]")); return; }
        go(urlAnnee(document.querySelector(sel + " .c-temps"), y), "replace");
      };
      step();
      timer = setInterval(step, 900);
    });
    // Courbes arrivées avec le contenu remplacé (celles de la page initiale sont déjà dessinées par charts.js).
    root.querySelectorAll(".line-chart").forEach((f) => {
      if (window.CPCharts && !f.querySelector(".plot svg")) window.CPCharts.line(f);
    });
  }

  window.addEventListener("popstate", () => go(window.location.href, "quiet"));
  const root = document.querySelector(sel);
  if (root) init(root);
})();

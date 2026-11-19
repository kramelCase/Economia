// Infobulles du lexique : survol et focus clavier (ordinateur), tap (mobile : 1er tap = infobulle,
// lien « Voir dans le lexique » dedans). Sans JavaScript, chaque terme reste un lien vers le lexique.
(function () {
  const data = JSON.parse((document.getElementById("tips") || {}).textContent || "{}");
  const tip = document.getElementById("tip");
  const t = window.I18N || {};
  const touch = window.matchMedia("(hover: none)").matches;
  let current = null;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  }

  function show(a) {
    const d = data[a.dataset.concept];
    if (!d || !tip) return;
    current = a;
    let body = d.statut === "a_sourcer" ? `<em>${esc(t.asourcer)}</em>` : esc(d.def);
    const notes = [];
    if (d.statut !== "a_sourcer" && !d.officielle) notes.push(t.nonoff);
    if (d.statut !== "a_sourcer" && d.langue !== document.documentElement.lang) notes.push(t.fr);
    tip.innerHTML = `<strong>${esc(d.terme)}</strong>${body}` +
      (d.src ? `<span class="tip-src">${esc(d.src)}${notes.length ? " · " + esc(notes.join(" ")) : ""}</span>` : "") +
      `<span class="tip-src"><a href="${a.getAttribute("href")}">${esc(t.voir)} →</a></span>`;
    tip.hidden = false;
    const r = a.getBoundingClientRect();
    const w = tip.offsetWidth;
    const left = Math.min(Math.max(8, r.left + window.scrollX), window.scrollX + document.documentElement.clientWidth - w - 8);
    tip.style.left = left + "px";
    tip.style.top = (r.bottom + window.scrollY + 6) + "px";
    a.setAttribute("aria-describedby", "tip");
  }

  function hide() {
    if (current) current.removeAttribute("aria-describedby");
    current = null;
    if (tip) tip.hidden = true;
  }

  document.querySelectorAll("a.terme").forEach((a) => {
    if (!touch) {
      a.addEventListener("mouseenter", () => show(a));
      a.addEventListener("mouseleave", () => setTimeout(() => { if (!tip.matches(":hover")) hide(); }, 120));
    }
    a.addEventListener("focus", () => show(a));
    a.addEventListener("blur", () => setTimeout(() => { if (!tip.contains(document.activeElement)) hide(); }, 120));
    a.addEventListener("click", (e) => {
      if (touch && current !== a) { e.preventDefault(); show(a); }
    });
  });
  if (tip) tip.addEventListener("mouseleave", hide);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  document.addEventListener("click", (e) => {
    if (current && !e.target.closest("a.terme") && !e.target.closest("#tip")) hide();
  });
})();

// Panneau d'exploration : exports image (le titre, la source et le lien sont dessinés dans l'image, ils ne
// se détachent pas du graphique) et copie du lien. Les réglages sont des liens : rien à faire ici.
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const wrap = document.querySelector(".s-chart");
  if (!wrap) return;

  // Fige les styles calculés (couleurs des variables CSS, police) : un SVG exporté n'a pas la feuille de style.
  function inline(src, dst) {
    const cs = getComputedStyle(src);
    ["fill", "fill-opacity", "stroke", "stroke-width", "opacity", "font-family", "font-size", "font-weight"]
      .forEach((k) => dst.setAttribute(k, cs.getPropertyValue(k)));
    [...src.children].forEach((c, i) => inline(c, dst.children[i]));
  }

  function composer() {
    const plot = wrap.querySelector(".plot svg");
    if (!plot) return null;
    const W = plot.viewBox.baseVal.width, H = plot.viewBox.baseVal.height;
    const top = 44, bottom = 40, cs = getComputedStyle(document.body);
    const out = document.createElementNS(NS, "svg");
    out.setAttribute("xmlns", NS);
    out.setAttribute("viewBox", `0 0 ${W} ${H + top + bottom}`);
    out.setAttribute("width", W); out.setAttribute("height", H + top + bottom);
    const bg = document.createElementNS(NS, "rect");
    bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", cs.backgroundColor);
    out.appendChild(bg);
    const text = (t, y, size, weight) => {
      const n = document.createElementNS(NS, "text");
      n.setAttribute("x", 12); n.setAttribute("y", y); n.setAttribute("font-size", size);
      n.setAttribute("font-weight", weight); n.setAttribute("fill", cs.color);
      n.setAttribute("font-family", cs.fontFamily); n.textContent = t;
      out.appendChild(n);
    };
    text(wrap.dataset.titre, 26, 15, 600);
    // Légende : nom de chaque série à côté de sa couleur.
    const g = document.createElementNS(NS, "g");
    g.setAttribute("transform", `translate(0 ${top})`);
    const clone = plot.cloneNode(true);
    inline(plot, clone);
    clone.querySelectorAll("[visibility=hidden], rect[fill=transparent]").forEach((n) => n.remove());
    while (clone.firstChild) g.appendChild(clone.firstChild);
    out.appendChild(g);
    let x = 12;
    wrap.querySelectorAll(".legend li").forEach((li) => {
      const sw = li.querySelector(".sw");
      const c = document.createElementNS(NS, "rect");
      c.setAttribute("x", x); c.setAttribute("y", top + H + 10); c.setAttribute("width", 10); c.setAttribute("height", 10);
      c.setAttribute("fill", getComputedStyle(sw).backgroundColor);
      out.appendChild(c);
      const n = document.createElementNS(NS, "text");
      n.setAttribute("x", x + 14); n.setAttribute("y", top + H + 19); n.setAttribute("font-size", 11);
      n.setAttribute("fill", cs.color); n.setAttribute("font-family", cs.fontFamily); n.textContent = li.textContent.trim();
      out.appendChild(n);
      x += 24 + li.textContent.trim().length * 6;
    });
    text(wrap.dataset.source, top + H + bottom - 4, 10, 400);
    return out;
  }

  function telecharger(blob, nom) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = nom;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  document.querySelectorAll("[data-export]").forEach((b) => b.addEventListener("click", () => {
    const svg = composer();
    if (!svg) return;
    const xml = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([xml], { type: "image/svg+xml" });
    if (b.dataset.export === "svg") return telecharger(blob, "comptes-publics-serie.svg");
    const img = new Image();
    img.onload = () => {
      const k = 2, cv = document.createElement("canvas");
      cv.width = img.width * k; cv.height = img.height * k;
      const ctx = cv.getContext("2d"); ctx.scale(k, k); ctx.drawImage(img, 0, 0);
      cv.toBlob((png) => png && telecharger(png, "comptes-publics-serie.png"), "image/png");
    };
    img.src = URL.createObjectURL(blob);
  }));

  document.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = b.dataset.done; } catch (e) { window.prompt("", b.dataset.copy); }
  }));
})();

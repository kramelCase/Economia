// Maquettes de la machine : un petit bâtiment ou objet par fonction de dépense (COFOG) et par acteur, façon maquette
// d'architecte en bois peint : arêtes biseautées, corniches, encadrements, perrons, socle. Elles nomment d'un coup d'œil ;
// le nom complet et le montant publié restent dans l'étiquette et l'infobulle. Chaque maquette tient dans un carré
// d'environ 1 × 1, posée sur y = 0, face vers +z.
import * as THREE from "/static/vendor/three-0.160.0.module.min.js";

const V = (x, y, z) => new THREE.Vector3(x, y, z);

// Boîte aux arêtes biseautées : la lumière accroche les arêtes, ce qui donne la matière d'une maquette en bois peint.
const BISEAUX = new Map();
function biseau(w, h, d) {
  const s = Math.min(0.022, Math.min(w, h, d) * 0.18);
  if (s < 0.006) return new THREE.BoxGeometry(w, h, d);
  const cle = `${w}|${h}|${d}`;
  if (BISEAUX.has(cle)) return BISEAUX.get(cle);
  const W = w / 2 - s, H = h / 2 - s, f = new THREE.Shape();
  f.moveTo(-W, -H); f.lineTo(W, -H); f.lineTo(W, H); f.lineTo(-W, H); f.closePath();
  const geo = new THREE.ExtrudeGeometry(f, { depth: d - 2 * s, bevelEnabled: true, bevelThickness: s, bevelSize: s,
                                            bevelSegments: 3, curveSegments: 4 });
  geo.translate(0, 0, -(d - 2 * s) / 2);
  geo.computeVertexNormals();
  BISEAUX.set(cle, geo);
  return geo;
}

function kit(g, M) {
  const add = (geo, mat, x, y, z) => {
    const m = new THREE.Mesh(geo, mat);
    m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true;
    g.add(m);
    return m;
  };
  const k = {
    add,
    // Boîte posée : (x, z) = centre au sol, y0 = bas.
    box: (w, h, d, mat, x = 0, y0 = 0, z = 0) => add(biseau(w, h, d), mat, x, y0 + h / 2, z),
    cyl: (r, h, mat, x = 0, y0 = 0, z = 0, seg = 32, r2 = r) => add(new THREE.CylinderGeometry(r, r2, h, Math.max(seg, 4)), mat, x, y0 + h / 2, z),
    cone: (r, h, mat, x = 0, y0 = 0, z = 0, seg = 24) => add(new THREE.ConeGeometry(r, h, seg), mat, x, y0 + h / 2, z),
    // Toit à deux pans : prisme le long de x, faîte en haut ; débord compris dans w et d.
    toit: (w, h, d, mat, x = 0, y0 = 0, z = 0) => {
      const geo = new THREE.CylinderGeometry(1, 1, w, 3);
      geo.rotateZ(Math.PI / 2); geo.rotateX(-Math.PI / 2);
      const m = add(geo, mat, x, y0 + h / 3, z);
      m.scale.set(1, h / 1.5, d / Math.sqrt(3));
      return m;
    },
    // Rangée de fenêtres : vitre éclairée de l'intérieur, encadrement clair et appui saillant.
    fenetres: (n, w, y, z, fw = 0.08, fh = 0.11, x0 = 0) => {
      for (let i = 0; i < n; i++) {
        const x = x0 - w / 2 + (i + 0.5) * (w / n);
        add(new THREE.BoxGeometry(fw + 0.022, fh + 0.022, 0.012), M.blanc, x, y, z);
        add(new THREE.BoxGeometry(fw, fh, 0.014), M.vitre, x, y, z + 0.003);
        add(new THREE.BoxGeometry(fw * 0.08, fh, 0.016), M.blanc, x, y, z + 0.004);
        add(biseau(fw + 0.04, 0.018, 0.04), M.blanc, x, y - fh / 2 - 0.012, z + 0.012);
      }
    },
    // Porte à encadrement, sur la façade avant.
    porte: (x, z, w = 0.1, h = 0.17, mat = M.bois) => {
      add(new THREE.BoxGeometry(w + 0.03, h + 0.02, 0.012), M.blanc, x, h / 2 + 0.01, z);
      add(new THREE.BoxGeometry(w, h, 0.016), mat, x, h / 2, z + 0.003);
    },
    // Corniche : un bandeau saillant en haut d'un mur.
    corniche: (w, d, y, mat = M.blanc, z = 0) => add(biseau(w + 0.05, 0.035, d + 0.05), mat, 0, y + 0.0175, z),
    // Perron : deux marches devant la porte.
    perron: (w, z, x = 0) => { add(biseau(w, 0.03, 0.12), M.pierre, x, 0.015, z + 0.06); add(biseau(w * 0.75, 0.03, 0.07), M.pierre, x, 0.045, z + 0.035); },
    drapeau: (x, y0, z, h, mats) => {
      add(new THREE.CylinderGeometry(0.01, 0.012, h, 8), M.metal, x, y0 + h / 2, z);
      add(new THREE.SphereGeometry(0.016, 10, 8), M.or, x, y0 + h + 0.01, z);
      mats.forEach((m, i) => add(new THREE.BoxGeometry(0.06, 0.11, 0.01), m, x + 0.032 + i * 0.06, y0 + h - 0.07, z));
    },
    // Colonnes à base et chapiteau.
    colonnes: (n, w, h, z, y0 = 0) => {
      for (let i = 0; i < n; i++) {
        const x = -w / 2 + (i + 0.5) * (w / n);
        add(new THREE.CylinderGeometry(0.03, 0.036, h - 0.05, 16), M.blanc, x, y0 + 0.025 + (h - 0.05) / 2, z);
        add(new THREE.BoxGeometry(0.085, 0.025, 0.085), M.blanc, x, y0 + 0.0125, z);
        add(new THREE.BoxGeometry(0.085, 0.025, 0.085), M.blanc, x, y0 + h - 0.0125, z);
      }
    },
    // Feuillage en volumes taillés (maquette), deux tons.
    arbre: (x, z, s = 1) => {
      add(new THREE.CylinderGeometry(0.03 * s, 0.045 * s, 0.22 * s, 10), M.bois, x, 0.11 * s, z);
      add(new THREE.IcosahedronGeometry(0.2 * s, 1), M.feuille, x, 0.33 * s, z);
      add(new THREE.IcosahedronGeometry(0.14 * s, 1), M.feuille2, x + 0.06 * s, 0.45 * s, z + 0.03 * s);
    },
    personne: (x, z, mat, s = 1) => {
      add(new THREE.CylinderGeometry(0.04 * s, 0.065 * s, 0.19 * s, 16), mat, x, 0.095 * s, z);
      add(new THREE.SphereGeometry(0.045 * s, 16, 12), M.peau, x, 0.24 * s, z);
    },
  };
  return k;
}

const MODELES = {
  // Services généraux des administrations : un immeuble de bureaux à drapeau.
  GF01: (k, M) => {
    k.box(0.82, 0.62, 0.55, M.mur);
    k.corniche(0.82, 0.55, 0.62);
    k.box(0.74, 0.04, 0.48, M.toitPlat, 0, 0.655);
    k.fenetres(5, 0.78, 0.47, 0.28); k.fenetres(5, 0.78, 0.29, 0.28);
    k.porte(0, 0.28, 0.14, 0.17, M.vitre); k.perron(0.3, 0.28);
    k.drapeau(0.3, 0.69, 0.05, 0.3, [M.bleu, M.blanc, M.rouge]);
  },
  // Défense : une tour crénelée à meurtrières.
  GF02: (k, M) => {
    k.cyl(0.32, 0.08, M.pierre2, 0, 0, 0, 40);
    k.cyl(0.28, 0.58, M.pierre, 0, 0.08, 0, 40, 0.3);
    k.cyl(0.31, 0.05, M.pierre2, 0, 0.64, 0, 40);
    for (let a = 0; a < 10; a++) k.box(0.09, 0.09, 0.07, M.pierre, Math.sin(a * Math.PI / 5) * 0.27, 0.69, Math.cos(a * Math.PI / 5) * 0.27).rotation.y = a * Math.PI / 5;
    for (const y of [0.25, 0.45]) k.add(new THREE.BoxGeometry(0.03, 0.09, 0.02), M.vitre, 0, y, 0.29);
    k.porte(0, 0.29, 0.12, 0.17);
    k.drapeau(0, 0.69, 0, 0.3, [M.bleu, M.blanc, M.rouge]);
  },
  // Ordre et sécurité : un poste à gyrophare.
  GF03: (k, M) => {
    k.box(0.72, 0.46, 0.5, M.mur);
    k.box(0.74, 0.07, 0.52, M.bleu, 0, 0.3);
    k.corniche(0.72, 0.5, 0.46, M.blanc);
    k.cyl(0.05, 0.05, M.metal, 0, 0.5, 0, 20);
    k.add(new THREE.SphereGeometry(0.055, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), M.gyro, 0, 0.55, 0);
    k.fenetres(2, 0.6, 0.18, 0.26, 0.1, 0.11, 0); k.porte(0, 0.26, 0.12, 0.2, M.bleu); k.perron(0.26, 0.26);
  },
  // Économie : une usine à toits en dents de scie et cheminée de briques.
  GF04: (k, M) => {
    k.box(0.82, 0.34, 0.55, M.brique);
    k.box(0.84, 0.03, 0.57, M.pierre, 0, 0.32);
    for (const x of [-0.27, 0, 0.27]) {
      k.toit(0.57, 0.2, 0.27, M.toitPlat, x, 0.35, 0).rotation.y = Math.PI / 2;
    }
    k.cyl(0.065, 0.78, M.brique, 0.31, 0, -0.16, 24, 0.085);
    k.cyl(0.075, 0.04, M.pierre2, 0.31, 0.74, -0.16, 24);
    k.fenetres(4, 0.78, 0.17, 0.28, 0.12, 0.12);
  },
  // Environnement : un bosquet.
  GF05: (k) => { k.arbre(-0.18, 0.05, 1.15); k.arbre(0.2, -0.12, 0.9); k.arbre(0.12, 0.2, 0.65); },
  // Logement : une maison à deux pans, cheminée et perron.
  GF06: (k, M) => {
    k.box(0.62, 0.36, 0.5, M.mur);
    k.toit(0.72, 0.3, 0.64, M.toit, 0, 0.36, 0);
    k.porte(-0.13, 0.25, 0.11, 0.2); k.perron(0.2, 0.25, -0.13);
    k.fenetres(1, 0.2, 0.2, 0.25, 0.12, 0.11, 0.14);
    k.box(0.09, 0.22, 0.09, M.brique, 0.17, 0.42, -0.1);
  },
  // Santé : un hôpital à croix rouge sur le fronton.
  GF07: (k, M) => {
    k.box(0.86, 0.5, 0.55, M.blanc);
    k.corniche(0.86, 0.55, 0.5, M.pierre);
    k.box(0.38, 0.2, 0.5, M.blanc, 0, 0.535);
    k.box(0.06, 0.16, 0.02, M.rouge, 0, 0.555, 0.255); k.box(0.16, 0.06, 0.02, M.rouge, 0, 0.605, 0.255);
    k.fenetres(5, 0.82, 0.36, 0.28, 0.08, 0.09); k.fenetres(4, 0.82, 0.16, 0.28, 0.08, 0.09);
    k.box(0.3, 0.025, 0.14, M.toitPlat, 0, 0.24, 0.34);
  },
  // Loisirs et culture : un temple à colonnes et fronton (musée, théâtre).
  GF08: (k, M) => {
    k.box(0.84, 0.05, 0.62, M.pierre2); k.box(0.78, 0.04, 0.56, M.pierre, 0, 0.05);
    k.box(0.68, 0.4, 0.3, M.mur, 0, 0.09, -0.1);
    k.colonnes(6, 0.74, 0.38, 0.2, 0.09);
    k.box(0.8, 0.05, 0.58, M.blanc, 0, 0.47);
    k.toit(0.8, 0.18, 0.58, M.pierre, 0, 0.52, 0);
  },
  // Enseignement : une école de briques à clocheton et horloge.
  GF09: (k, M) => {
    k.box(0.86, 0.38, 0.5, M.brique);
    k.corniche(0.86, 0.5, 0.36, M.blanc);
    k.toit(0.94, 0.18, 0.6, M.toit, 0, 0.395, 0);
    k.box(0.2, 0.34, 0.2, M.brique, 0, 0.38, 0.05);
    k.cone(0.17, 0.22, M.toit, 0, 0.72, 0.05, 4).rotation.y = Math.PI / 4;
    const h = k.cyl(0.065, 0.02, M.blanc, 0, 0, 0.16, 28); h.rotation.x = Math.PI / 2; h.position.y = 0.58;
    k.fenetres(4, 0.84, 0.21, 0.26, 0.11, 0.12); k.perron(0.24, 0.26);
  },
  // Protection sociale : un parapluie au-dessus d'une famille.
  GF10: (k, M) => {
    k.cyl(0.012, 0.66, M.metal, 0.02, 0, 0, 10);
    const c = k.cone(0.46, 0.18, M.accent, 0.02, 0.6, 0, 8); c.rotation.y = Math.PI / 8;
    k.add(new THREE.SphereGeometry(0.02, 10, 8), M.or, 0.02, 0.8, 0);
    k.personne(-0.17, 0.06, M.bleu); k.personne(0.17, 0.04, M.rouge); k.personne(0.01, 0.17, M.vert, 0.68);
  },
  // Administrations centrales : un palais à colonnes et fronton, drapeau.
  S1311: (k, M) => {
    k.box(1.02, 0.05, 0.72, M.pierre2); k.box(0.96, 0.04, 0.66, M.pierre, 0, 0.05);
    k.box(0.9, 0.5, 0.42, M.mur, 0, 0.09, -0.12);
    k.colonnes(6, 0.88, 0.48, 0.2, 0.09);
    k.box(0.98, 0.05, 0.66, M.blanc, 0, 0.57);
    k.toit(0.98, 0.22, 0.66, M.pierre, 0, 0.62, 0);
    k.drapeau(0, 0.77, -0.12, 0.34, [M.bleu, M.blanc, M.rouge]);
  },
  // Administrations locales : une mairie à beffroi et horloge.
  S1313: (k, M) => {
    k.box(0.92, 0.44, 0.5, M.mur);
    k.corniche(0.92, 0.5, 0.42);
    k.toit(1.0, 0.22, 0.6, M.toit, 0, 0.455, 0);
    k.box(0.26, 0.48, 0.26, M.mur, 0, 0.42, 0.05);
    k.cone(0.22, 0.26, M.toit, 0, 0.9, 0.05, 4).rotation.y = Math.PI / 4;
    const h = k.cyl(0.075, 0.02, M.blanc, 0, 0, 0.19, 28); h.rotation.x = Math.PI / 2; h.position.y = 0.72;
    k.fenetres(4, 0.88, 0.27, 0.26, 0.08, 0.13); k.porte(0, 0.26, 0.12, 0.18); k.perron(0.3, 0.26);
    k.drapeau(0.38, 0.6, 0.05, 0.28, [M.bleu, M.blanc, M.rouge]);
  },
  // Sécurité sociale : un guichet à auvent, où l'on vient en personne.
  S1314: (k, M) => {
    k.box(0.92, 0.5, 0.5, M.mur);
    k.corniche(0.92, 0.5, 0.48);
    k.box(0.84, 0.04, 0.48, M.toitPlat, 0, 0.52);
    k.box(0.8, 0.025, 0.22, M.accent, 0, 0.3, 0.34).rotation.x = 0.28;
    k.box(0.56, 0.24, 0.02, M.vitre, 0, 0.03, 0.255);
    k.fenetres(4, 0.84, 0.41, 0.26, 0.08, 0.08);
    k.personne(-0.3, 0.44, M.bleu); k.personne(0.28, 0.46, M.rouge); k.personne(0.36, 0.4, M.vert, 0.7);
  },
  // --- Recettes : d'où vient l'argent ---
  // Cotisations sociales : des bureaux où l'on travaille, salariés devant (employeurs et ménages paient).
  D61REC: (k, M) => {
    k.box(0.78, 0.56, 0.5, M.mur);
    k.corniche(0.78, 0.5, 0.56);
    k.box(0.7, 0.04, 0.44, M.toitPlat, 0, 0.595);
    k.fenetres(4, 0.74, 0.43, 0.26); k.fenetres(4, 0.74, 0.25, 0.26);
    k.porte(0, 0.26, 0.13, 0.16, M.vitre);
    k.personne(-0.26, 0.42, M.bleu); k.personne(-0.12, 0.46, M.rouge); k.personne(0.22, 0.44, M.vert);
  },
  // Impôts sur la production et les importations (TVA…) : une rangée de commerces à auvents.
  D2REC: (k, M) => {
    [[-0.3, M.rouge], [0, M.bleu], [0.3, M.vert]].forEach(([x, m]) => {
      k.box(0.28, 0.4, 0.46, M.mur, x);
      k.box(0.3, 0.035, 0.48, M.toitPlat, x, 0.4);
      k.box(0.22, 0.16, 0.02, M.vitre, x, 0.03, 0.235);
      k.box(0.27, 0.02, 0.13, m, x, 0.24, 0.3).rotation.x = 0.35;
      k.fenetres(1, 0.2, 0.32, 0.235, 0.09, 0.06, x);
    });
    k.add(new THREE.BoxGeometry(0.1, 0.07, 0.07), M.bois, 0.42, 0.035, 0.35);
    k.add(new THREE.BoxGeometry(0.07, 0.06, 0.06), M.bois, 0.44, 0.1, 0.35);
  },
  // Impôts courants sur le revenu (ménages et sociétés) : immeubles d'habitation et tour de bureaux.
  D5REC: (k, M) => {
    k.box(0.32, 0.86, 0.36, M.vitre, 0.22, 0, -0.06);
    for (let y = 0.12; y < 0.86; y += 0.14) k.box(0.34, 0.02, 0.38, M.blanc, 0.22, y, -0.06);
    k.box(0.36, 0.5, 0.4, M.mur, -0.2, 0, 0.02);
    k.box(0.4, 0.04, 0.44, M.toitPlat, -0.2, 0.5, 0.02);
    k.fenetres(2, 0.32, 0.38, 0.225, 0.08, 0.09, -0.2); k.fenetres(2, 0.32, 0.22, 0.225, 0.08, 0.09, -0.2);
    k.porte(-0.2, 0.225, 0.09, 0.12);
    k.arbre(0.43, 0.3, 0.5);
  },
  // Ventes et production : une gare de services publics payants, horloge et marquise.
  P11_P12_P131: (k, M) => {
    k.box(0.84, 0.4, 0.46, M.pierre);
    k.corniche(0.84, 0.46, 0.4);
    k.toit(0.9, 0.2, 0.56, M.toitPlat, 0, 0.435, 0);
    const h = k.cyl(0.08, 0.02, M.blanc, 0, 0, 0.25, 28); h.rotation.x = Math.PI / 2; h.position.y = 0.3;
    k.box(0.7, 0.025, 0.2, M.accent, 0, 0.18, 0.33);
    for (const x of [-0.32, 0.32]) k.cyl(0.012, 0.18, M.metal, x, 0, 0.42, 8);
    k.fenetres(4, 0.8, 0.1, 0.24, 0.1, 0.12);
  },
  // Autres recettes (revenus de la propriété, transferts…) : un entrepôt à caisses.
  AUTRES: (k, M) => {
    k.box(0.74, 0.34, 0.5, M.pierre2);
    k.toit(0.8, 0.14, 0.56, M.toitPlat, 0, 0.34, 0);
    k.box(0.26, 0.24, 0.02, M.bois, -0.12, 0, 0.255);
    for (const [x, y] of [[0.22, 0], [0.34, 0], [0.28, 0.1]]) k.box(0.1, 0.1, 0.1, M.bois, x, y, 0.36);
  },
  // Déficit public : le besoin de financement, couvert par l'emprunt ; une salle de marché à colonnes.
  B9: (k, M) => {
    k.box(0.8, 0.04, 0.56, M.pierre2); k.box(0.74, 0.04, 0.5, M.pierre, 0, 0.04);
    k.box(0.64, 0.4, 0.3, M.mur, 0, 0.08, -0.08);
    k.colonnes(4, 0.66, 0.38, 0.16, 0.08);
    k.box(0.74, 0.05, 0.5, M.blanc, 0, 0.46);
    k.toit(0.74, 0.16, 0.5, M.toit, 0, 0.51, 0);
  },
};
for (const c of ["D4REC", "D7REC", "D9REC", "D39REC"]) MODELES[c] = MODELES.AUTRES;

// Socle : pelouse sous les arbres et le parapluie, pierre sous les bâtiments.
const PELOUSE = new Set(["GF05", "GF10"]);

// Modèles Kenney (City Kit, licence CC0, static/vendor/kenney) : [kit/fichier, x, z, rotation] en unités Kenney ;
// le groupe est ensuite ramené à la taille d'une maquette (carré d'environ 1 × 1). Prioritaires sur MODELES.
const KENNEY = {
  D61REC: [["commercial/building-e", -0.55, 0, 0], ["suburban/building-type-b", 0.6, 0.1, 0]],
  D2REC: [["commercial/building-a", -0.55, 0, 0], ["commercial/building-c", 0.55, 0, 0]],
  D5REC: [["commercial/building-skyscraper-c", -0.5, -0.1, 0], ["suburban/building-type-d", 0.65, 0.15, 0]],
  P11_P12_P131: [["industrial/building-g", 0, 0, 0]],
  AUTRES: [["industrial/building-s", -0.3, 0, 0], ["industrial/shipping-container-a", 0.85, 0.2, Math.PI / 2]],
  GF01: [["commercial/building-skyscraper-a", 0, 0, 0]],
  GF04: [["industrial/building-m", 0, 0, 0]],
  GF05: [["industrial/windmill", -0.45, -0.2, 0], ["industrial/solar-panel-landscape-group", 0.4, 0.1, 0],
         ["suburban/tree-large", -0.5, 0.45, 0]],
  GF06: [["suburban/building-type-e", -0.55, 0, 0], ["suburban/building-type-h", 0.6, 0, 0]],
  // [kit/fichier, x, z, rotation, échelle, posé sur la pièce précédente]
  GF02: [["castle-kit/tower-square-base", -0.4, 0, 0], ["castle-kit/tower-square-mid-windows", -0.4, 0, 0, 1, true],
         ["castle-kit/tower-square-top-roof-high", -0.4, 0, 0, 1, true], ["castle-kit/wall-narrow", 0.6, 0, 0],
         ["castle-kit/flag-pennant", 0.6, 0, 0, 1, true]],
  GF03: [["commercial/building-d", 0, -0.2, 0], ["car-kit/police", 0.85, 0.55, -Math.PI / 2, 0.3]],
  GF07: [["commercial/building-i", 0, -0.2, 0], ["car-kit/ambulance", 0.9, 0.55, -Math.PI / 2, 0.3]],
  GF08: [["commercial/building-h", -0.3, 0, 0], ["commercial/detail-parasol-a", 0.6, 0.35, 0],
         ["commercial/detail-parasol-b", 0.6, -0.25, 0]],
  GF09: [["commercial/building-f", 0, 0, 0], ["suburban/tree-small", 0.75, 0.3, 0], ["suburban/tree-small", -0.75, 0.3, 0]],
  GF10: [["suburban/building-type-a", -0.6, 0, 0], ["suburban/building-type-c", 0.6, 0, 0], ["suburban/planter", 0, 0.55, 0]],
  B9: [["commercial/building-skyscraper-d", 0, 0, 0]],
  S1311: [["commercial/building-n", 0, 0, 0]],
  S1313: [["commercial/building-j", 0, 0, 0], ["suburban/tree-large", 0.85, 0.35, 0]],
  S1314: [["commercial/building-l", 0, 0, 0]],
};
for (const c of ["D4REC", "D7REC", "D9REC", "D39REC"]) KENNEY[c] = KENNEY.AUTRES;
const GLB = new Map();

// Reconstruit un modèle écrit en clair (nœuds, sommets, faces, matières) ; la texture est la palette du kit.
const PALETTES = new Map();
function enClair(d, dossier) {
  if (!PALETTES.has(dossier)) {
    const t = new THREE.TextureLoader().load(`${dossier}Textures/colormap.png`);
    t.flipY = false; t.colorSpace = THREE.SRGBColorSpace;
    PALETTES.set(dossier, t);
  }
  const mats = d.mats.map((m) => new THREE.MeshStandardMaterial({
    color: new THREE.Color().setRGB(m.c[0], m.c[1], m.c[2], THREE.LinearSRGBColorSpace), metalness: m.m, roughness: m.r,
    map: m.t ? PALETTES.get(dossier) : null }));
  const noeud = (n) => {
    const o = new THREE.Group();
    if (n.matrix) o.applyMatrix4(new THREE.Matrix4().fromArray(n.matrix));
    if (n.translation) o.position.fromArray(n.translation);
    if (n.rotation) o.quaternion.fromArray(n.rotation);
    if (n.scale) o.scale.fromArray(n.scale);
    for (const p of n.p || []) {
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.Float32BufferAttribute(p.pos, 3));
      if (p.nor) g.setAttribute("normal", new THREE.Float32BufferAttribute(p.nor, 3)); else g.computeVertexNormals();
      if (p.uv) g.setAttribute("uv", new THREE.Float32BufferAttribute(p.uv, 2));
      if (p.idx) g.setIndex(p.idx);
      o.add(new THREE.Mesh(g, p.mat != null ? mats[p.mat] : new THREE.MeshStandardMaterial()));
    }
    for (const e of n.e) o.add(noeud(e));
    return o;
  };
  const s = new THREE.Group();
  for (const r of d.racines) s.add(noeud(r));
  return s;
}

// Charge une fois tous les fichiers Kenney utilisés ; un fichier manquant laisse la maquette dessinée à la main.
export async function charger() {
  let l = null;  // GLTFLoader, chargé seulement s'il sert (la copie de démo n'en a pas besoin)
  const fichiers = new Set(Object.values(KENNEY).flat().map((e) => e[0]));
  const lire = async (f) => {
    const u = new URL(`./vendor/kenney/${f}.glb`, import.meta.url).href;
    if (!u.endsWith(".json")) {
      l ||= new (await import("./vendor/three-addons/GLTFLoader.js")).GLTFLoader();
      return l.loadAsync(u);
    }
    // Copie de démo : l'hébergement ne sert pas les .glb ; le modèle y est en clair dans un .json (tmp/_demo.py).
    return { scene: enClair(await (await fetch(u)).json(), u.slice(0, u.lastIndexOf("/") + 1)) };
  };
  await Promise.all([...fichiers].map((f) => lire(f).then((g) => GLB.set(f, g.scene)).catch(() => {})));
}

function kenney(g, code) {
  const parts = KENNEY[code];
  if (!parts || !parts.every((e) => GLB.has(e[0]))) return false;
  const inner = new THREE.Group();
  let dessus = 0;
  for (const [f, x, z, r, ech = 1, pile = false] of parts) {
    const m = GLB.get(f).clone();
    m.scale.setScalar(ech);
    m.position.set(x, pile ? dessus : 0, z); m.rotation.y = r;
    m.updateMatrixWorld(true);
    dessus = new THREE.Box3().setFromObject(m).max.y;
    m.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    inner.add(m);
  }
  const b = new THREE.Box3().setFromObject(inner), s = Math.min(1.0 / Math.max(b.max.x - b.min.x, b.max.z - b.min.z), 0.9 / (b.max.y - b.min.y));
  inner.scale.setScalar(s);
  inner.position.set(-(b.min.x + b.max.x) / 2 * s, -b.min.y * s, -(b.min.z + b.max.z) / 2 * s);
  g.add(inner);
  return true;
}

export function maquette(code, M) {
  const g = new THREE.Group();
  const f = MODELES[code];
  if (!kenney(g, code)) {
    if (!f) return g;
    f(kit(g, M), M);
  }
  const b = new THREE.Box3().setFromObject(g), w = b.max.x - b.min.x + 0.12, d = b.max.z - b.min.z + 0.12;
  const s = new THREE.Mesh(biseau(Math.max(w, 0.5), 0.04, Math.max(d, 0.5)), PELOUSE.has(code) ? M.pelouse : M.pierre2);
  s.position.set((b.min.x + b.max.x) / 2, -0.02, (b.min.z + b.max.z) / 2); s.receiveShadow = true;
  g.add(s);
  return g;
}
export const MAQUETTES = new Set([...Object.keys(MODELES), ...Object.keys(KENNEY)]);
export { V, biseau };

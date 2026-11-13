/* art.js — ilustrasi alat berat (SVG inline, tanpa file gambar, jalan offline) */
const ART = (() => {
  const Y = "#F5B700", YD = "#D89A00", D = "#2b2f36", D2 = "#3a3f48", G = "#BFE3F2", GR = "#9aa3ad";
  const wheel = (cx, cy, r) =>
    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="#23262c"/><circle cx="${cx}" cy="${cy}" r="${r * 0.5}" fill="${GR}"/><circle cx="${cx}" cy="${cy}" r="${r * 0.18}" fill="#23262c"/>`;
  const shadow = `<ellipse cx="100" cy="114" rx="92" ry="4" fill="#000" opacity=".13"/>`;

  const parts = {
    Excavator: `${shadow}
      <rect x="26" y="92" width="116" height="21" rx="10.5" fill="${D}"/>
      <circle cx="38" cy="102.5" r="6.5" fill="#4a505a"/><circle cx="66" cy="104" r="4.5" fill="#4a505a"/>
      <circle cx="92" cy="104" r="4.5" fill="#4a505a"/><circle cx="118" cy="104" r="4.5" fill="#4a505a"/>
      <circle cx="130" cy="102.5" r="6.5" fill="#4a505a"/>
      <rect x="44" y="84" width="82" height="9" rx="2" fill="${D2}"/>
      <path d="M40 84 V62 Q40 56 46 56 H106 V84 Z" fill="${Y}"/>
      <rect x="36" y="60" width="14" height="24" rx="4" fill="${YD}"/>
      <rect x="56" y="45" width="5" height="13" fill="${D2}"/>
      <path d="M80 56 V34 Q80 29 85 29 H110 Q114 29 116 33 L122 56 Z" fill="${Y}"/>
      <path d="M87 36 H108 L112 50 H87 Z" fill="${G}"/><path d="M87 36 H92 V50 H87Z" fill="#fff" opacity=".4"/>
      <path d="M108 60 L140 20 L153 26 L127 70 Z" fill="${Y}"/>
      <path d="M114 50 L136 36" stroke="${GR}" stroke-width="4" stroke-linecap="round"/>
      <path d="M146 22 L158 26 L186 66 L175 72 Z" fill="${YD}"/>
      <path d="M174 66 L195 60 L196 82 Q186 90 176 80 Z" fill="${D}"/>
      <path d="M178 85 l2 5 m5 -6 l2 5 m5 -8 l2 5" stroke="${GR}" stroke-width="2" stroke-linecap="round"/>
      <circle cx="148" cy="24" r="3" fill="${D}"/>`,

    Bulldozer: `${shadow}
      <path d="M32 80 L16 100 L23 105 L40 90 Z" fill="${D}"/>
      <rect x="34" y="84" width="114" height="27" rx="13.5" fill="${D}"/>
      <circle cx="49" cy="97.5" r="8" fill="#4a505a"/><circle cx="133" cy="97.5" r="8" fill="#4a505a"/>
      <circle cx="72" cy="102" r="5" fill="#4a505a"/><circle cx="91" cy="102" r="5" fill="#4a505a"/><circle cx="110" cy="102" r="5" fill="#4a505a"/>
      <path d="M56 86 V60 Q56 54 62 54 H112 L128 68 V86 Z" fill="${Y}"/>
      <rect x="112" y="40" width="4" height="16" fill="${D2}"/>
      <rect x="62" y="26" width="42" height="30" rx="3" fill="${Y}"/>
      <rect x="67" y="32" width="32" height="20" rx="2" fill="${G}"/><rect x="67" y="32" width="6" height="20" fill="#fff" opacity=".4"/>
      <rect x="58" y="22" width="50" height="6" rx="2" fill="${D}"/>
      <path d="M126 80 L156 92" stroke="${D2}" stroke-width="7" stroke-linecap="round"/>
      <path d="M150 54 Q172 52 177 58 L173 106 Q160 107 152 100 Z" fill="${YD}"/>
      <path d="M173 106 L177 58" stroke="${D}" stroke-width="4"/>`,

    "Dump Truck": `${shadow}
      <rect x="14" y="86" width="176" height="8" rx="2" fill="${D2}"/>
      <path d="M16 50 H124 L118 86 H22 Z" fill="${Y}"/>
      <path d="M40 54 V84 M64 54 V84 M88 54 V84 M112 54 L109 84" stroke="${YD}" stroke-width="3"/>
      <rect x="12" y="45" width="114" height="7" rx="2" fill="${YD}"/>
      <path d="M132 86 V58 Q132 50 140 50 H162 L180 70 V86 Z" fill="${Y}"/>
      <path d="M140 57 H159 L171 70 H140 Z" fill="${G}"/>
      <rect x="177" y="76" width="7" height="5" fill="#fff7c2"/>
      ${wheel(44, 98, 15)}${wheel(82, 98, 15)}${wheel(160, 98, 15)}`,

    "Wheel Loader": `${shadow}
      <path d="M22 86 V58 Q22 52 28 52 H84 V86 Z" fill="${Y}"/>
      <rect x="22" y="56" width="10" height="26" rx="3" fill="${YD}"/>
      <path d="M52 52 V28 Q52 24 56 24 H80 Q84 24 85 28 L90 52 Z" fill="${Y}"/>
      <path d="M58 31 H78 L82 46 H58 Z" fill="${G}"/>
      <rect x="84" y="60" width="36" height="26" rx="2" fill="${YD}"/>
      <path d="M102 62 L146 44 L151 53 L110 74 Z" fill="${Y}"/>
      <path d="M96 72 L130 52" stroke="${GR}" stroke-width="4" stroke-linecap="round"/>
      <path d="M140 40 L188 42 L182 80 Q162 88 144 78 Z" fill="${D}"/>
      <path d="M186 42 L182 80" stroke="${GR}" stroke-width="3"/>
      ${wheel(56, 97, 18)}${wheel(120, 97, 18)}`,

    "Vibrator Roller": `${shadow}
      <rect x="40" y="60" width="34" height="17" rx="3" fill="${YD}"/>
      <path d="M68 58 H148 Q158 58 158 68 V84 H68 Z" fill="${Y}"/>
      <rect x="106" y="22" width="48" height="6" rx="2" fill="${D}"/>
      <path d="M110 28 V58 M150 28 V58" stroke="${D}" stroke-width="3"/>
      <rect x="120" y="42" width="16" height="16" rx="2" fill="${D2}"/>
      <circle cx="52" cy="88" r="25" fill="#8d96a1"/><circle cx="52" cy="88" r="14" fill="#6b7480"/>
      <circle cx="52" cy="88" r="4" fill="${D}"/>
      <path d="M32 88 H72 M52 68 V108" stroke="#fff" stroke-width="1.5" opacity=".25"/>
      <circle cx="150" cy="93" r="20" fill="#23262c"/><circle cx="150" cy="93" r="9" fill="${GR}"/><circle cx="150" cy="93" r="3" fill="#23262c"/>`,

    Crane: `${shadow}
      <rect x="10" y="86" width="180" height="8" rx="2" fill="${D2}"/>
      <rect x="20" y="62" width="110" height="24" rx="3" fill="${Y}"/>
      <path d="M134 86 V62 Q134 56 140 56 H164 L182 74 V86 Z" fill="${Y}"/>
      <path d="M141 62 H161 L172 74 H141 Z" fill="${G}"/>
      <path d="M44 64 L52 56 L176 8 L180 17 Z" fill="${Y}"/>
      <path d="M62 56 L68 63 M80 50 L86 58 M98 43 L104 52 M116 36 L122 45 M134 30 L140 39 M152 23 L158 32" stroke="${YD}" stroke-width="2.5"/>
      <path d="M176 15 V62" stroke="${D}" stroke-width="1.6"/>
      <path d="M176 62 v6 a4 4 0 1 1 -4 4" fill="none" stroke="${D}" stroke-width="2.4" stroke-linecap="round"/>
      <rect x="62" y="86" width="6" height="14" fill="${D2}"/><rect x="62" y="98" width="22" height="4" rx="1" fill="${D2}"/>
      ${wheel(40, 98, 13)}${wheel(92, 98, 13)}${wheel(150, 98, 13)}`,

    Lainnya: `<ellipse cx="100" cy="114" rx="60" ry="4" fill="#000" opacity=".13"/>
      <path d="M52 86 Q52 34 100 34 Q148 34 148 86 Z" fill="${Y}"/>
      <rect x="92" y="28" width="16" height="58" fill="${YD}" opacity=".7"/>
      <rect x="40" y="86" width="120" height="13" rx="6.5" fill="${YD}"/>
      <path d="M62 62 Q66 48 80 44" stroke="#fff" stroke-width="4" stroke-linecap="round" fill="none" opacity=".5"/>`,
  };

  function svg(cat, cls = "") {
    const body = parts[cat] || parts.Lainnya;
    return `<svg class="art ${cls}" viewBox="0 0 200 120" role="img" aria-label="${cat || "Alat berat"}">${body}</svg>`;
  }

  /* panorama untuk banner dashboard */
  function hero() {
    const m = (cat, x, y, w) => `<svg x="${x}" y="${y}" width="${w}" height="${w * 0.6}" viewBox="0 0 200 120">${parts[cat]}</svg>`;
    return `<svg class="hero-art" viewBox="0 0 520 170" preserveAspectRatio="xMaxYMax slice" aria-hidden="true">
      <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe9a8"/><stop offset="1" stop-color="#fff6dc"/></linearGradient></defs>
      <rect width="520" height="170" fill="url(#sky)"/>
      <circle cx="430" cy="42" r="26" fill="#F5B700" opacity=".85"/>
      <path d="M0 120 Q90 70 190 110 T380 100 T520 105 V170 H0 Z" fill="#d9c9a0"/>
      <path d="M0 140 Q120 105 250 135 T520 130 V170 H0 Z" fill="#b9a574"/>
      <rect y="150" width="520" height="20" fill="#8e7c52"/>
      ${m("Dump Truck", 20, 62, 150)}${m("Excavator", 170, 38, 200)}${m("Bulldozer", 330, 58, 160)}
    </svg>`;
  }

  return { svg, hero, categories: Object.keys(parts).filter(k => k !== "Lainnya").concat("Lainnya") };
})();

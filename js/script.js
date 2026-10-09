const birds = [
  {
    id: 1,
    tag: 'raptor',
    name: 'Peregrine Falcon',
    sci: 'Falco peregrinus',
    family: 'Falconidae',
    hatch: 'Fledges at 6 weeks old',
    life: '15–20 years in the wild',
    wing: '100–110 cm (39–43 in)',
    habitat: 'Cliffs, coastlines, and skyscraper ledges — nearly every continent',
    diet: 'Birds, taken mid-air in a stoop',
    status: 'lc',
    statusText: 'Least Concern',
    call: 'A sharp, rapid "kek-kek-kek" alarm near the nest',
    stat: 'TOP SPEED · 390 km/h dive',
    notes: 'Treats a 40-storey ledge exactly like a cliff face. In its hunting stoop it is the fastest living animal on Earth — folding its wings and letting gravity do the work.',
    color: '#C99A3E',
    svg: `<svg viewBox="0 0 120 120"><path d="M60 20 C50 30 20 40 5 55 C25 50 45 48 55 55 C50 65 45 85 40 100 C55 90 62 78 65 62 C70 78 78 90 90 100 C88 85 82 65 78 55 C88 48 100 50 115 55 C100 40 70 30 60 20Z" fill="#C99A3E" opacity="0.9"/><circle cx="60" cy="34" r="4" fill="#2A2118"/></svg>`
  },
  {
    id: 2,
    tag: 'tropical',
    name: 'Scarlet Macaw',
    sci: 'Ara macao',
    family: 'Psittacidae',
    hatch: 'Leaves the nest around 3 months old',
    life: '40–50 years, some past 75',
    wing: '~110 cm (43 in)',
    habitat: 'Lowland rainforest canopy, Central &amp; South America',
    diet: 'Fruit, nuts, seeds, and mineral-rich clay',
    status: 'lc',
    statusText: 'Least Concern (regionally threatened)',
    call: 'A loud, raucous screech; skilled mimic in captivity',
    stat: 'BONDS · Mates for life',
    notes: 'Visits riverbank clay licks in flocks — the minerals neutralize toxins in the unripe fruit that makes up much of its diet.',
    color: '#B1502F',
    svg: `<svg viewBox="0 0 120 120"><path d="M55 15 Q40 25 42 45 Q30 60 20 100 Q35 90 45 65 Q50 80 48 105 Q60 90 58 60 Q65 80 68 105 Q78 85 70 60 Q85 50 100 40 Q78 38 62 42 Q58 25 55 15Z" fill="#B1502F"/><circle cx="52" cy="30" r="3.5" fill="#2A2118"/></svg>`
  },
  {
    id: 3,
    tag: 'water',
    name: 'Snowy Owl',
    sci: 'Bubo scandiacus',
    family: 'Strigidae',
    hatch: 'Hatches after ~32 days incubation',
    life: '~10 years wild (28 recorded in care)',
    wing: '125–150 cm (4.2–4.9 ft)',
    habitat: 'Arctic tundra; winters across open farmland and coasts',
    diet: 'Lemmings and other small mammals, sometimes birds',
    status: 'vu',
    statusText: 'Vulnerable',
    call: 'A deep, hoarse hooting bark, carried far over open ground',
    stat: 'HUNTS · By daylight, unlike most owls',
    notes: 'Feathers grow whiter with every year of age. Because Arctic summers never fully darken, this owl hunts at all hours — a habit that carries into its winter range.',
    color: '#EFC873',
    svg: `<svg viewBox="0 0 120 120"><ellipse cx="60" cy="60" rx="38" ry="42" fill="#EFC873"/><circle cx="46" cy="52" r="9" fill="#2A2118"/><circle cx="74" cy="52" r="9" fill="#2A2118"/><path d="M60 60 L54 70 L66 70Z" fill="#B1502F"/></svg>`
  },
  {
    id: 4,
    tag: 'raptor',
    name: 'Bald Eagle',
    sci: 'Haliaeetus leucocephalus',
    family: 'Accipitridae',
    hatch: 'First flight at 10–12 weeks old',
    life: '20–30 years in the wild',
    wing: '180–230 cm (6–7.5 ft)',
    habitat: 'Rivers, lakes, and coastlines across North America',
    diet: "Mainly fish, snatched from the water's surface",
    status: 'lc',
    statusText: 'Least Concern (recovered)',
    call: 'A surprisingly thin, high chirping whistle',
    stat: 'NEST WEIGHT · Up to 2,700 kg',
    notes: 'Builds the largest tree nest of any North American bird, adding to the same nest year after year until branches groan under its weight.',
    color: '#6E8F73',
    svg: `<svg viewBox="0 0 120 120"><path d="M60 25 C40 35 10 45 5 60 C25 55 45 55 58 60 C55 75 50 90 45 105 C58 95 65 82 65 65 C65 82 72 95 85 105 C80 90 75 75 72 60 C85 55 105 55 125 60 C120 45 90 35 60 25Z" fill="#EEEEEE"/><path d="M55 30 Q60 45 65 30" fill="none"/><ellipse cx="60" cy="35" rx="7" ry="9" fill="#EEEEEE"/><path d="M56 36 L60 42 L64 36Z" fill="#C99A3E"/></svg>`
  },
  {
    id: 5,
    tag: 'tropical',
    name: 'Ruby-throated Hummingbird',
    sci: 'Archilochus colubris',
    family: 'Trochilidae',
    hatch: 'Leaves the nest at 18–22 days old',
    life: '3–5 years, occasionally longer',
    wing: '~11 cm (4.3 in)',
    habitat: 'Gardens and forest edges, eastern North America',
    diet: 'Flower nectar and small soft-bodied insects',
    status: 'lc',
    statusText: 'Least Concern',
    call: 'A thin, high-pitched chip; wings hum near 50 beats/second',
    stat: 'MIGRATION · 800 km non-stop over open sea',
    notes: 'Crosses the Gulf of Mexico in a single flight with no rest stop, having roughly doubled its body weight beforehand to fuel the crossing. Heart rate can reach 1,200 bpm mid-flight.',
    color: '#B1502F',
    svg: `<svg viewBox="0 0 120 120"><ellipse cx="55" cy="60" rx="14" ry="9" fill="#6E8F73"/><path d="M40 60 L15 55" stroke="#2A2118" stroke-width="2"/><path d="M65 55 Q90 30 100 15" stroke="#6E8F73" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M65 65 Q90 90 100 105" stroke="#6E8F73" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.6"/></svg>`
  },
  {
    id: 6,
    tag: 'water',
    name: 'Emperor Penguin',
    sci: 'Aptenodytes forsteri',
    family: 'Spheniscidae',
    hatch: "Egg incubated on the father's feet, ~65 days",
    life: '15–20 years',
    wing: 'Flipper span ~35 cm (flightless)',
    habitat: 'Antarctic sea ice and surrounding open water',
    diet: 'Fish, krill, and squid, caught on deep dives',
    status: 'nt',
    statusText: 'Near Threatened',
    call: 'A low, individually distinct trumpeting song for mate and chick recognition',
    stat: 'FAST · Fathers fast up to 4 months',
    notes: 'While the egg balances on his feet through the polar winter, the father eats nothing at all — surviving on stored fat alone until the mother returns from the sea.',
    color: '#A9C0B6',
    svg: `<svg viewBox="0 0 120 120"><ellipse cx="60" cy="70" rx="26" ry="38" fill="#2A2118"/><ellipse cx="60" cy="78" rx="15" ry="28" fill="#F3E8C9"/><circle cx="60" cy="35" r="16" fill="#2A2118"/><path d="M56 38 L48 42 L56 44Z" fill="#C99A3E"/></svg>`
  },
  {
    id: 7,
    tag: 'water',
    name: 'Common Kingfisher',
    sci: 'Alcedo atthis',
    family: 'Alcedinidae',
    hatch: 'Fledges at 23–27 days old',
    life: '~2 years average (up to 15 recorded)',
    wing: '24–26 cm (9–10 in)',
    habitat: 'Still and slow rivers across Europe, Asia, and North Africa',
    diet: 'Small fish and aquatic insects, taken in a vertical dive',
    status: 'lc',
    statusText: 'Least Concern',
    call: 'A bright, sharp "tsee" whistled in flight',
    stat: 'DIVE · Enters water at ~40 km/h',
    notes: "A transparent third eyelid shields its eyes the instant it hits the water. Its beak shape — cutting the surface with almost no splash — is said to have inspired the nose of Japan's bullet train.",
    color: '#6E8F73',
    svg: `<svg viewBox="0 0 120 120"><ellipse cx="65" cy="60" rx="24" ry="17" fill="#6E8F73"/><path d="M45 55 L15 50 L45 62Z" fill="#C99A3E"/><circle cx="80" cy="52" r="4" fill="#2A2118"/><path d="M55 75 Q60 95 65 100" stroke="#2A2118" stroke-width="2" fill="none"/></svg>`
  },
  {
    id: 8,
    tag: 'water',
    name: 'Atlantic Puffin',
    sci: 'Fratercula arctica',
    family: 'Alcidae',
    hatch: 'Fledges at 38–44 days, alone, at night',
    life: '~20 years',
    wing: '47–63 cm (18.5–25 in)',
    habitat: 'North Atlantic sea cliffs and open ocean',
    diet: 'Small fish such as sand eels and herring',
    status: 'vu',
    statusText: 'Vulnerable',
    call: 'A low, growling "arr" from inside the burrow',
    stat: 'CARRY · 10+ fish crosswise in one beak',
    notes: 'Backward-hinged spines on its tongue and palate let it grip additional fish while still holding the last, so it can keep fishing after a catch. It effectively "flies" underwater on stubby wings.',
    color: '#B1502F',
    svg: `<svg viewBox="0 0 120 120"><ellipse cx="60" cy="70" rx="24" ry="32" fill="#2A2118"/><ellipse cx="60" cy="80" rx="13" ry="20" fill="#F3E8C9"/><path d="M50 55 L35 50 L50 62Z" fill="#B1502F"/><path d="M50 58 L35 55 L50 65Z" fill="#EFC873"/><circle cx="60" cy="45" r="12" fill="#2A2118"/></svg>`
  },
  {
    id: 9,
    tag: 'raptor',
    name: 'Wandering Albatross',
    sci: 'Diomedea exulans',
    family: 'Diomedeidae',
    hatch: 'Fledges at ~9 months — longest of any bird',
    life: '50+ years',
    wing: 'up to 3.5 m (11.5 ft) — largest of any living bird',
    habitat: 'The Southern Ocean, circling the globe',
    diet: 'Squid, fish, and scavenged carrion at the surface',
    status: 'vu',
    statusText: 'Vulnerable',
    call: 'Largely silent at sea; bill-clacking and braying during courtship on land',
    stat: 'GLIDE · 500+ km a day, wings barely moving',
    notes: 'Rides wind gradients off the ocean surface in a technique called dynamic soaring, allowing it to glide for hours — sometimes days — without a single wingbeat.',
    color: '#A9C0B6',
    svg: `<svg viewBox="0 0 120 120"><path d="M60 55 C20 45 5 30 2 20 C15 35 35 45 58 50 C62 45 65 40 60 30 C68 38 70 48 65 55 C88 45 105 35 118 20 C115 30 100 45 60 55Z" fill="#A9C0B6"/><circle cx="60" cy="60" r="5" fill="#2A2118"/></svg>`
  }
];

const grid = document.getElementById('grid');

function renderCards(list) {
  grid.innerHTML = '';

  list.forEach((b, i) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.animationDelay = (i * 0.06) + 's';

    card.innerHTML = `
      <div class="specimen-no">
        <span>SPECIMEN NO. 0${b.id}</span>
        <span>${b.family.toUpperCase()}</span>
      </div>

      <div class="card-illus">${b.svg}</div>
      <h3 class="card-name">${b.name}</h3>
      <p class="card-sci">${b.sci}</p>
      <div class="card-stat">${b.stat}</div>
      <div class="card-tap">Open Dossier →</div>
    `;

    card.addEventListener('click', () => openDossier(b));
    grid.appendChild(card);

    requestAnimationFrame(() => card.classList.add('reveal'));
  });
}

renderCards(birds);

// ---- Filters ----

const search = document.getElementById('search');
const chips = document.querySelectorAll('.chip');

let activeFilter = 'all';

function applyFilters() {
  const q = search.value.trim().toLowerCase();

  const list = birds.filter(b => {
    const matchesTag = activeFilter === 'all' || b.tag === activeFilter;
    const matchesQ = !q || (b.name + b.sci + b.family + b.habitat).toLowerCase().includes(q);

    return matchesTag && matchesQ;
  });

  renderCards(list);
}

search.addEventListener('input', applyFilters);

chips.forEach(c => {
  c.addEventListener('click', () => {
    chips.forEach(x => x.classList.remove('active'));
    c.classList.add('active');

    activeFilter = c.dataset.f;
    applyFilters();
  });
});

// ---- Dossier modal ----

const scrim = document.getElementById('scrim');
const dName = document.getElementById('dName');
const dSci = document.getElementById('dSci');
const dIllus = document.getElementById('dIllus');
const dFields = document.getElementById('dFields');
const dNotes = document.getElementById('dNotes');
const stamp = document.getElementById('stamp');

function statusClass(s) {
  return s === 'lc' ? 'status-lc' : s === 'nt' ? 'status-nt' : 'status-vu';
}

function openDossier(b) {
  dName.textContent = b.name;
  dSci.textContent = b.sci + ' · ' + b.family;
  dIllus.innerHTML = b.svg;

  const fieldData = [
    ['Hatched', b.hatch],
    ['Typical Lifespan', b.life],
    ['Wingspan', b.wing],
    ['Habitat', b.habitat],
    ['Diet', b.diet],
    ['Call', b.call]
  ];

  dFields.innerHTML = fieldData.map(([label, val]) => `
    <div class="field">
      <div class="field-label">${label}</div>
      <div class="field-val">${val}</div>
    </div>
  `).join('') + `
    <div class="field full">
      <div class="field-label">Conservation Status</div>
      <div class="field-val">
        <span class="status-tag ${statusClass(b.status)}">${b.statusText}</span>
      </div>
    </div>
  `;

  dNotes.innerHTML = `
    <div class="field-label" style="margin-bottom:8px;">Field Notes</div>
    ${b.notes}
  `;

  dNotes.classList.remove('show');

  stamp.style.animation = 'none';
  void stamp.offsetWidth;
  stamp.style.animation = '';

  scrim.classList.add('open');
  document.body.style.overflow = 'hidden';

  // Staggered reveal
  const fieldEls = dFields.querySelectorAll('.field');

  fieldEls.forEach((el, i) => {
    el.classList.remove('show');
    setTimeout(() => el.classList.add('show'), 500 + i * 110);
  });

  setTimeout(() => {
    dNotes.classList.add('show');
  }, 500 + fieldEls.length * 110 + 150);
}

function closeDossier() {
  scrim.classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('closeBtn').addEventListener('click', closeDossier);

scrim.addEventListener('click', (e) => {
  if (e.target === scrim) closeDossier();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeDossier();
});

// ---- Flying flock in hero ----

const flockEl = document.getElementById('flock');

const flockSVG = `
  <svg viewBox="0 0 60 30" fill="#EFC873">
    <path d="M0 15 Q15 0 30 15 Q45 0 60 15 Q45 12 30 20 Q15 12 0 15Z"/>
  </svg>
`;

function spawnBird() {
  const el = document.createElement('div');
  el.innerHTML = flockSVG;

  const svg = el.firstElementChild;

  svg.style.animation = `flyAcross ${5 + Math.random() * 3}s linear forwards`;
  svg.style.top = (10 + Math.random() * 50) + '%';

  flockEl.appendChild(svg);

  setTimeout(() => svg.remove(), 9000);
}

if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  for (let i = 0; i < 5; i++) {
    setTimeout(spawnBird, i * 450);
  }

  setInterval(() => {
    if (Math.random() > 0.4) spawnBird();
  }, 3200);
}

// ---- Magnetic tilt on cards ----

document.addEventListener('mousemove', (e) => {
  document.querySelectorAll('.card').forEach(card => {
    const r = card.getBoundingClientRect();

    if (
      e.clientX < r.left - 40 ||
      e.clientX > r.right + 40 ||
      e.clientY < r.top - 40 ||
      e.clientY > r.bottom + 40
    ) {
      return;
    }

    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;

    card.style.transform =
      `perspective(700px) rotateX(${py * -6}deg) rotateY(${px * 6}deg) translateY(-2px)`;
  });
});

document.addEventListener('mouseleave', () => {
  document.querySelectorAll('.card').forEach(c => {
    c.style.transform = '';
  });
});
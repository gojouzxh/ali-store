const birds = [
  {
    id: 1,
    tag: 'budgie',
    name: 'Grey/White',
    sci: null,
    family: null,
    hatch: 'March 12, 2025',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Spacious flight cage with natural perches, food and water bowls, and toys',
    diet: 'Budgie seed mix or formulated pellets, leafy greens, and safe vegetables',
    status: null,
    statusText: null,
    call: 'Soft chirping, tweeting, and contact calls',
    stat: null,
    notes: null,
    photo: 'images/bird-01.jpg',
    photoAlt: 'Grey and white budgie'
  },
  {
    id: 2,
    tag: 'budgie',
    name: 'Pale Yellow Budgies',
    sci: null,
    family: null,
    hatch: 'April 5, 2025',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Spacious flight cage with natural perches, food and water bowls, and toys',
    diet: 'Budgie seed mix or formulated pellets, leafy greens, and safe vegetables',
    status: null,
    statusText: null,
    call: 'Soft chirping, tweeting, and contact calls',
    stat: null,
    notes: null,
    photo: 'images/bird-02.jpg',
    photoAlt: 'Pale yellow budgies'
  },
  {
    id: 3,
    tag: 'budgie',
    name: 'Lutino Yellow',
    sci: null,
    family: null,
    hatch: 'January 20, 2025',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Secure flight cage with horizontal bars, perches, toys, and room to move',
    diet: 'Quality budgie seed mix or pellets, leafy greens, carrots, and clean drinking water',
    status: null,
    statusText: null,
    call: 'Cheerful chirps, whistles, and short chatter',
    stat: null,
    notes: null,
    photo: 'images/bird-03.jpg',
    photoAlt: 'Yellow lutino budgie'
  },
  {
    id: 4,
    tag: 'budgie',
    name: 'Green Budgies',
    sci: null,
    family: null,
    hatch: 'February 14, 2025',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Secure flight cage with horizontal bars, perches, toys, and room to move',
    diet: 'Quality budgie seed mix or pellets, leafy greens, carrots, and clean drinking water',
    status: null,
    statusText: null,
    call: 'Cheerful chirps, whistles, and short chatter',
    stat: null,
    notes: null,
    photo: 'images/bird-04.jpg',
    photoAlt: 'Green budgies'
  },
  {
    id: 5,
    tag: 'budgie',
    name: 'Blue/Violet Budgie',
    sci: null,
    family: null,
    hatch: 'May 8, 2025',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Flight cage with natural wood perches, enrichment toys, and daily opportunities for safe exercise',
    diet: 'Budgie pellets or seed mix, leafy vegetables, and occasional safe fruit',
    status: null,
    statusText: null,
    call: 'High-pitched chirping, whistles, and flock contact calls',
    stat: null,
    notes: null,
    photo: 'images/bird-05.jpg',
    photoAlt: 'Blue and violet budgie'
  },
  {
    id: 6,
    tag: 'budgie',
    name: 'Yellow Lutino Budgie',
    sci: null,
    family: null,
    hatch: 'June 18, 2025',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Spacious cage with perches at different heights, toys, and a shaded resting area',
    diet: 'Budgie seed mix or pellets, fresh greens, and safe vegetables',
    status: null,
    statusText: null,
    call: 'Light chirping, squeaks, and melodic whistles',
    stat: null,
    notes: null,
    photo: 'images/bird-06.jpg',
    photoAlt: 'Yellow lutino budgie'
  },
  {
    id: 7,
    tag: 'budgie',
    name: 'Yellow Lutino (Pair record)',
    sci: null,
    family: null,
    hatch: 'November 22, 2024',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Flight cage with multiple perches, enrichment toys, and separate feeding spaces',
    diet: 'Balanced budgie seed mix or pellets, leafy greens, vegetables, and fresh water',
    status: null,
    statusText: null,
    call: 'Chirping, whistles, and social chatter',
    stat: null,
    notes: null,
    photo: 'images/bird-07.jpg',
    photoAlt: 'Yellow lutino budgie pair'
  },
  {
    id: 8,
    tag: 'budgie',
    name: 'Blue (Pair record)',
    sci: null,
    family: null,
    hatch: 'December 10, 2024',
    life: '7-12 years',
    wing: '25-30 cm',
    habitat: 'Flight cage with multiple perches, enrichment toys, and separate feeding spaces',
    diet: 'Balanced budgie seed mix or pellets, leafy greens, vegetables, and fresh water',
    status: null,
    statusText: null,
    call: 'Chirping, whistles, and social chatter',
    stat: null,
    notes: null,
    photo: 'images/bird-08.jpg',
    photoAlt: 'Blue budgie pair'
  },
  {
    id: 9,
    tag: 'lovebird',
    name: 'Blue Lovebirds',
    sci: null,
    family: null,
    hatch: 'July 19, 2025',
    life: '10-15 years',
    wing: '24-28 cm',
    habitat: 'Secure cage with sturdy perches, chew toys, and space for climbing and flapping',
    diet: 'Lovebird pellets or a balanced seed mix, leafy greens, safe vegetables, and clean water',
    status: null,
    statusText: null,
    call: 'Loud chirps, squeaks, and short squawks',
    stat: null,
    notes: null,
    photo: 'images/bird-09.jpg',
    photoAlt: 'Blue lovebirds'
  }
];

const grid = document.getElementById('grid');
const search = document.getElementById('search');
const chips = document.querySelectorAll('.chip');

function hasValue(value) {
  return value !== null && value !== undefined && value !== '';
}

function createTextElement(tagName, className, value) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = String(value);
  return element;
}

function appendOptionalText(parent, tagName, className, value) {
  if (!hasValue(value)) return null;
  const element = createTextElement(tagName, className, value);
  parent.appendChild(element);
  return element;
}

function createPhotoFrame(photo, photoAlt, className) {
  const frame = document.createElement('div');
  frame.className = className;

  const image = document.createElement('img');
  image.className = 'bird-photo';
  image.alt = hasValue(photoAlt) ? photoAlt : '';
  image.loading = 'lazy';

  const placeholder = document.createElement('div');
  placeholder.className = 'photo-placeholder';
  placeholder.textContent = 'Photo unavailable';
  placeholder.hidden = true;

  image.onerror = () => {
    image.hidden = true;
    placeholder.hidden = false;
  };

  if (hasValue(photo)) {
    image.src = photo;
  } else {
    image.hidden = true;
    placeholder.hidden = false;
  }

  frame.append(image, placeholder);
  return frame;
}

function renderCards(list) {
  grid.replaceChildren();

  list.forEach((bird, index) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.animationDelay = `${index * 0.06}s`;

    const specimen = document.createElement('div');
    specimen.className = 'specimen-no';
    specimen.appendChild(createTextElement('span', '', `SPECIMEN NO. ${String(bird.id).padStart(2, '0')}`));
    specimen.appendChild(createTextElement('span', '', bird.tag.toUpperCase()));
    card.appendChild(specimen);

    card.appendChild(createPhotoFrame(bird.photo, bird.photoAlt, 'card-illus'));

    card.appendChild(createTextElement('h3', 'card-name', bird.name));
    appendOptionalText(card, 'p', 'card-sci', bird.sci);
    appendOptionalText(card, 'div', 'card-stat', bird.stat);
    card.appendChild(createTextElement('div', 'card-tap', 'Open Dossier →'));

    card.addEventListener('click', () => openDossier(bird));
    grid.appendChild(card);
    requestAnimationFrame(() => card.classList.add('reveal'));
  });
}

renderCards(birds);

// ---- Filters ----

let activeFilter = 'all';

function applyFilters() {
  const query = search.value.trim().toLowerCase();
  const list = birds.filter((bird) => {
    const matchesTag = activeFilter === 'all' || bird.tag === activeFilter;
    const searchableValues = [bird.name, bird.sci, bird.family, bird.habitat]
      .filter(hasValue)
      .join(' ')
      .toLowerCase();
    return matchesTag && (!query || searchableValues.includes(query));
  });

  renderCards(list);
}

search.addEventListener('input', applyFilters);

chips.forEach((chip) => {
  chip.addEventListener('click', () => {
    chips.forEach((item) => item.classList.remove('active'));
    chip.classList.add('active');
    activeFilter = chip.dataset.f;
    applyFilters();
  });
});

// ---- Dossier modal ----

const scrim = document.getElementById('scrim');
const dName = document.getElementById('dName');
const dSci = document.getElementById('dSci');
const dPhoto = document.getElementById('dPhoto');
const dFields = document.getElementById('dFields');
const dNotes = document.getElementById('dNotes');
const stamp = document.getElementById('stamp');

function statusClass(status) {
  return status === 'lc' ? 'status-lc' : status === 'nt' ? 'status-nt' : 'status-vu';
}

function appendDossierField(label, value, className = 'field') {
  if (!hasValue(value)) return null;
  const field = document.createElement('div');
  field.className = className;
  field.appendChild(createTextElement('div', 'field-label', label));
  field.appendChild(createTextElement('div', 'field-val', value));
  dFields.appendChild(field);
  return field;
}

function openDossier(bird) {
  dName.textContent = bird.name;
  const identity = [bird.sci, bird.family].filter(hasValue).join(' · ');
  dSci.textContent = identity;
  dSci.hidden = !identity;

  const photoFrame = createPhotoFrame(bird.photo, bird.photoAlt, 'dossier-illus');
  dPhoto.replaceChildren(...photoFrame.childNodes);
  dFields.replaceChildren();
  [
    ['Hatched', bird.hatch],
    ['Typical Lifespan', bird.life],
    ['Wingspan', bird.wing],
    ['Habitat', bird.habitat],
    ['Diet', bird.diet],
    ['Call', bird.call]
  ].forEach(([label, value]) => appendDossierField(label, value));

  if (hasValue(bird.statusText)) {
    const field = document.createElement('div');
    field.className = 'field full';
    field.appendChild(createTextElement('div', 'field-label', 'Conservation Status'));
    const value = createTextElement('span', `status-tag ${statusClass(bird.status)}`, bird.statusText);
    const valueContainer = document.createElement('div');
    valueContainer.className = 'field-val';
    valueContainer.appendChild(value);
    field.appendChild(valueContainer);
    dFields.appendChild(field);
  }

  dNotes.replaceChildren();
  if (hasValue(bird.notes)) {
    dNotes.appendChild(createTextElement('div', 'field-label', 'Field Notes'));
    dNotes.appendChild(document.createTextNode(bird.notes));
    dNotes.hidden = false;
  } else {
    dNotes.hidden = true;
  }
  dNotes.classList.remove('show');

  stamp.style.animation = 'none';
  void stamp.offsetWidth;
  stamp.style.animation = '';

  scrim.classList.add('open');
  document.body.style.overflow = 'hidden';

  const fieldElements = dFields.querySelectorAll('.field');
  fieldElements.forEach((element, index) => {
    element.classList.remove('show');
    setTimeout(() => element.classList.add('show'), 500 + index * 110);
  });

  if (hasValue(bird.notes)) {
    setTimeout(() => dNotes.classList.add('show'), 500 + fieldElements.length * 110 + 150);
  }
}

function closeDossier() {
  scrim.classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('closeBtn').addEventListener('click', closeDossier);

scrim.addEventListener('click', (event) => {
  if (event.target === scrim) closeDossier();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeDossier();
});

// ---- Flying flock in hero ----

const flockEl = document.getElementById('flock');
const svgNamespace = 'http://www.w3.org/2000/svg';

function createFlockSvg() {
  const svg = document.createElementNS(svgNamespace, 'svg');
  svg.setAttribute('viewBox', '0 0 60 30');
  svg.setAttribute('fill', '#EFC873');
  const path = document.createElementNS(svgNamespace, 'path');
  path.setAttribute('d', 'M0 15 Q15 0 30 15 Q45 0 60 15 Q45 12 30 20 Q15 12 0 15Z');
  svg.appendChild(path);
  return svg;
}

function spawnBird() {
  const svg = createFlockSvg();
  svg.style.animation = `flyAcross ${5 + Math.random() * 3}s linear forwards`;
  svg.style.top = `${10 + Math.random() * 50}%`;
  flockEl.appendChild(svg);
  setTimeout(() => svg.remove(), 9000);
}

if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  for (let index = 0; index < 5; index += 1) {
    setTimeout(spawnBird, index * 450);
  }

  setInterval(() => {
    if (Math.random() > 0.4) spawnBird();
  }, 3200);
}

// ---- Magnetic tilt on cards ----

document.addEventListener('mousemove', (event) => {
  document.querySelectorAll('.card').forEach((card) => {
    const rect = card.getBoundingClientRect();
    if (
      event.clientX < rect.left - 40 ||
      event.clientX > rect.right + 40 ||
      event.clientY < rect.top - 40 ||
      event.clientY > rect.bottom + 40
    ) {
      return;
    }

    const px = (event.clientX - rect.left) / rect.width - 0.5;
    const py = (event.clientY - rect.top) / rect.height - 0.5;
    card.style.transform =
      `perspective(700px) rotateX(${py * -6}deg) rotateY(${px * 6}deg) translateY(-2px)`;
  });
});

document.addEventListener('mouseleave', () => {
  document.querySelectorAll('.card').forEach((card) => {
    card.style.transform = '';
  });
});

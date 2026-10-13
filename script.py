"""Browser-side Python behavior for the bird catalog, loaded by PyScript."""

from __future__ import annotations

from dataclasses import dataclass

from py import Math, document, window  # pyright: ignore[reportMissingImports]

try:
    from pyodide.ffi import create_proxy  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover - fallback for non-Pyodide runtimes
    class _FallbackProxy:
        def __init__(self, callback):
            self._callback = callback

        def __call__(self, *args, **kwargs):
            return self._callback(*args, **kwargs)

        def destroy(self):
            self._callback = None

    def create_proxy(callback):
        return _FallbackProxy(callback)


_callback_refs = []


@dataclass(frozen=True)
class Bird:
    id: int
    tag: str
    name: str
    sci: str | None
    family: str | None
    hatch: str
    life: str
    wing: str
    habitat: str
    diet: str
    status: str | None
    status_text: str | None
    call: str
    stat: str | None
    notes: str | None
    photo: str
    photo_alt: str


BIRDS = (
    Bird(
        id=1,
        tag="budgie",
        name="Grey/White",
        sci=None,
        family=None,
        hatch="March 12, 2025",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Spacious flight cage with natural perches, food and water bowls, and toys",
        diet="Budgie seed mix or formulated pellets, leafy greens, and safe vegetables",
        status=None,
        status_text=None,
        call="Soft chirping, tweeting, and contact calls",
        stat=None,
        notes=None,
        photo="images/bird-01.jpg",
        photo_alt="Grey and white budgie",
    ),
    Bird(
        id=2,
        tag="budgie",
        name="Pale Yellow Budgies",
        sci=None,
        family=None,
        hatch="April 5, 2025",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Spacious flight cage with natural perches, food and water bowls, and toys",
        diet="Budgie seed mix or formulated pellets, leafy greens, and safe vegetables",
        status=None,
        status_text=None,
        call="Soft chirping, tweeting, and contact calls",
        stat=None,
        notes=None,
        photo="images/bird-02.jpg",
        photo_alt="Pale yellow budgies",
    ),
    Bird(
        id=3,
        tag="budgie",
        name="Lutino Yellow",
        sci=None,
        family=None,
        hatch="January 20, 2025",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Secure flight cage with horizontal bars, perches, toys, and room to move",
        diet="Quality budgie seed mix or pellets, leafy greens, carrots, and clean drinking water",
        status=None,
        status_text=None,
        call="Cheerful chirps, whistles, and short chatter",
        stat=None,
        notes=None,
        photo="images/bird-03.jpg",
        photo_alt="Yellow lutino budgie",
    ),
    Bird(
        id=4,
        tag="budgie",
        name="Green Budgies",
        sci=None,
        family=None,
        hatch="February 14, 2025",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Secure flight cage with horizontal bars, perches, toys, and room to move",
        diet="Quality budgie seed mix or pellets, leafy greens, carrots, and clean drinking water",
        status=None,
        status_text=None,
        call="Cheerful chirps, whistles, and short chatter",
        stat=None,
        notes=None,
        photo="images/bird-04.jpg",
        photo_alt="Green budgies",
    ),
    Bird(
        id=5,
        tag="budgie",
        name="Blue/Violet Budgie",
        sci=None,
        family=None,
        hatch="May 8, 2025",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Flight cage with natural wood perches, enrichment toys, and daily opportunities for safe exercise",
        diet="Budgie pellets or seed mix, leafy vegetables, and occasional safe fruit",
        status=None,
        status_text=None,
        call="High-pitched chirping, whistles, and flock contact calls",
        stat=None,
        notes=None,
        photo="images/bird-05.jpg",
        photo_alt="Blue and violet budgie",
    ),
    Bird(
        id=6,
        tag="budgie",
        name="Yellow Lutino Budgie",
        sci=None,
        family=None,
        hatch="June 18, 2025",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Spacious cage with perches at different heights, toys, and a shaded resting area",
        diet="Budgie seed mix or pellets, fresh greens, and safe vegetables",
        status=None,
        status_text=None,
        call="Light chirping, squeaks, and melodic whistles",
        stat=None,
        notes=None,
        photo="images/bird-06.jpg",
        photo_alt="Yellow lutino budgie",
    ),
    Bird(
        id=7,
        tag="budgie",
        name="Yellow Lutino (Pair record)",
        sci=None,
        family=None,
        hatch="November 22, 2024",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Flight cage with multiple perches, enrichment toys, and separate feeding spaces",
        diet="Balanced budgie seed mix or pellets, leafy greens, vegetables, and fresh water",
        status=None,
        status_text=None,
        call="Chirping, whistles, and social chatter",
        stat=None,
        notes=None,
        photo="images/bird-07.jpg",
        photo_alt="Yellow lutino budgie pair",
    ),
    Bird(
        id=8,
        tag="budgie",
        name="Blue (Pair record)",
        sci=None,
        family=None,
        hatch="December 10, 2024",
        life="7-12 years",
        wing="25-30 cm",
        habitat="Flight cage with multiple perches, enrichment toys, and separate feeding spaces",
        diet="Balanced budgie seed mix or pellets, leafy greens, vegetables, and fresh water",
        status=None,
        status_text=None,
        call="Chirping, whistles, and social chatter",
        stat=None,
        notes=None,
        photo="images/bird-08.jpg",
        photo_alt="Blue budgie pair",
    ),
    Bird(
        id=9,
        tag="lovebird",
        name="Blue Lovebirds",
        sci=None,
        family=None,
        hatch="July 19, 2025",
        life="10-15 years",
        wing="24-28 cm",
        habitat="Secure cage with sturdy perches, chew toys, and space for climbing and flapping",
        diet="Lovebird pellets or a balanced seed mix, leafy greens, safe vegetables, and clean water",
        status=None,
        status_text=None,
        call="Loud chirps, squeaks, and short squawks",
        stat=None,
        notes=None,
        photo="images/bird-09.jpg",
        photo_alt="Blue lovebirds",
    ),
)


def _keep_callback(callback):
    proxy = create_proxy(callback)
    _callback_refs.append(proxy)
    return proxy


def _schedule(callback, delay=None, animation_frame=False):
    proxy = None

    def invoke(*args):
        try:
            callback(*args)
        finally:
            proxy.destroy()
            _callback_refs.remove(proxy)

    proxy = _keep_callback(invoke)
    if animation_frame:
        window.requestAnimationFrame(proxy)
    else:
        window.setTimeout(proxy, delay)


def _bind(element, event_name, callback, capture=False):
    element.addEventListener(
        event_name, _keep_callback(callback), capture
    )


def _text_element(tag_name, class_name, value):
    element = document.createElement(tag_name)
    element.className = class_name
    element.textContent = str(value)
    return element


def _append_optional_text(parent, tag_name, class_name, value):
    if value is None or value == "":
        return None
    element = _text_element(tag_name, class_name, value)
    parent.appendChild(element)
    return element


def _create_photo_frame(photo, photo_alt, class_name):
    frame = document.createElement("div")
    frame.className = class_name

    image = document.createElement("img")
    image.className = "bird-photo"
    image.alt = photo_alt or ""
    image.loading = "lazy"
    image.hidden = not bool(photo)

    placeholder = _text_element("div", "photo-placeholder", "Photo unavailable")
    placeholder.hidden = bool(photo)

    if photo:
        image.src = photo

    frame.append(image, placeholder)
    return frame


def _render_cards(birds):
    grid.replaceChildren()

    for index, bird in enumerate(birds):
        card = document.createElement("div")
        card.className = "card"
        card.dataset.specimenId = str(bird.id)
        card.style.animationDelay = f"{index * 0.06}s"

        specimen = document.createElement("div")
        specimen.className = "specimen-no"
        specimen.appendChild(
            _text_element("span", "", f"SPECIMEN NO. {bird.id:02d}")
        )
        specimen.appendChild(_text_element("span", "", bird.tag.upper()))
        card.appendChild(specimen)

        card.appendChild(_create_photo_frame(bird.photo, bird.photo_alt, "card-illus"))
        card.appendChild(_text_element("h3", "card-name", bird.name))
        _append_optional_text(card, "p", "card-sci", bird.sci)
        _append_optional_text(card, "div", "card-stat", bird.stat)
        card.appendChild(_text_element("div", "card-tap", "Open Dossier →"))
        grid.appendChild(card)
        _schedule(
            lambda _timestamp, item=card: item.classList.add("reveal"),
            animation_frame=True,
        )


grid = document.getElementById("grid")
search = document.getElementById("search")
chips = document.querySelectorAll(".chip")
scrim = document.getElementById("scrim")
d_name = document.getElementById("dName")
d_sci = document.getElementById("dSci")
d_photo = document.getElementById("dPhoto")
d_fields = document.getElementById("dFields")
d_notes = document.getElementById("dNotes")
stamp = document.getElementById("stamp")
active_filter = "all"


def _apply_filters(*_args):
    query = search.value.strip().casefold()
    matching_birds = []
    for bird in BIRDS:
        if active_filter != "all" and bird.tag != active_filter:
            continue
        searchable_values = " ".join(
            value
            for value in (bird.name, bird.sci, bird.family, bird.habitat)
            if value
        ).casefold()
        if not query or query in searchable_values:
            matching_birds.append(bird)
    _render_cards(matching_birds)


def _append_dossier_field(label, value, class_name="field"):
    if value is None or value == "":
        return None
    field = document.createElement("div")
    field.className = class_name
    field.appendChild(_text_element("div", "field-label", label))
    field.appendChild(_text_element("div", "field-val", value))
    d_fields.appendChild(field)
    return field


def _status_class(status):
    if status == "lc":
        return "status-lc"
    if status == "nt":
        return "status-nt"
    return "status-vu"


def _open_dossier(bird):
    d_name.textContent = bird.name
    identity = " · ".join(value for value in (bird.sci, bird.family) if value)
    d_sci.textContent = identity
    d_sci.hidden = not bool(identity)

    photo_frame = _create_photo_frame(bird.photo, bird.photo_alt, "dossier-illus")
    d_photo.replaceChildren(*photo_frame.childNodes)
    d_fields.replaceChildren()
    fields = (
        ("Hatched", bird.hatch),
        ("Typical Lifespan", bird.life),
        ("Wingspan", bird.wing),
        ("Habitat", bird.habitat),
        ("Diet", bird.diet),
        ("Call", bird.call),
    )
    for label, value in fields:
        _append_dossier_field(label, value)

    if bird.status_text:
        field = document.createElement("div")
        field.className = "field full"
        field.appendChild(
            _text_element("div", "field-label", "Conservation Status")
        )
        value = _text_element(
            "span", f"status-tag {_status_class(bird.status)}", bird.status_text
        )
        value_container = document.createElement("div")
        value_container.className = "field-val"
        value_container.appendChild(value)
        field.appendChild(value_container)
        d_fields.appendChild(field)

    d_notes.replaceChildren()
    if bird.notes:
        d_notes.appendChild(_text_element("div", "field-label", "Field Notes"))
        d_notes.appendChild(document.createTextNode(bird.notes))
        d_notes.hidden = False
    else:
        d_notes.hidden = True
    d_notes.classList.remove("show")

    stamp.style.animation = "none"
    _ = stamp.offsetWidth
    stamp.style.animation = ""
    scrim.classList.add("open")
    document.body.style.overflow = "hidden"

    field_elements = d_fields.querySelectorAll(".field")
    for index, element in enumerate(field_elements):
        element.classList.remove("show")
        _schedule(
            lambda item=element: item.classList.add("show"),
            500 + index * 110,
        )

    if bird.notes:
        _schedule(
            lambda: d_notes.classList.add("show"),
            500 + len(field_elements) * 110 + 150,
        )


def _close_dossier(*_args):
    scrim.classList.remove("open")
    document.body.style.overflow = ""


def _on_grid_click(event):
    card = event.target.closest(".card")
    if card is None:
        return
    specimen_id = int(card.dataset.specimenId)
    bird = next(item for item in BIRDS if item.id == specimen_id)
    _open_dossier(bird)


def _on_chip_click(event):
    global active_filter
    selected_chip = event.currentTarget
    for chip in chips:
        chip.classList.remove("active")
    selected_chip.classList.add("active")
    active_filter = selected_chip.dataset.f
    _apply_filters()


def _on_scrim_click(event):
    if event.target == scrim:
        _close_dossier()


def _on_keydown(event):
    if event.key == "Escape":
        _close_dossier()


def _on_photo_error(event):
    image = event.target
    if image.classList.contains("hero-logo"):
        image.hidden = True
        image.parentElement.hidden = True
        return
    if not image.classList.contains("bird-photo"):
        return
    image.hidden = True
    placeholder = image.parentElement.querySelector(".photo-placeholder")
    placeholder.hidden = False


_render_cards(BIRDS)
_bind(search, "input", _apply_filters)
for chip in chips:
    _bind(chip, "click", _on_chip_click)
_bind(grid, "click", _on_grid_click)
_bind(document.getElementById("closeBtn"), "click", _close_dossier)
_bind(scrim, "click", _on_scrim_click)
_bind(document, "keydown", _on_keydown)
_bind(document.body, "error", _on_photo_error, capture=True)


def _create_flock_svg():
    namespace = "http://www.w3.org/2000/svg"
    svg = document.createElementNS(namespace, "svg")
    svg.setAttribute("viewBox", "0 0 60 30")
    svg.setAttribute("fill", "#EFC873")
    path = document.createElementNS(namespace, "path")
    path.setAttribute(
        "d", "M0 15 Q15 0 30 15 Q45 0 60 15 Q45 12 30 20 Q15 12 0 15Z"
    )
    svg.appendChild(path)
    return svg


def _spawn_bird():
    flock = document.getElementById("flock")
    svg = _create_flock_svg()
    svg.style.animation = f"flyAcross {5 + Math.random() * 3}s linear forwards"
    svg.style.top = f"{10 + Math.random() * 50}%"
    flock.appendChild(svg)
    _schedule(lambda: svg.remove(), 9000)


if not window.matchMedia("(prefers-reduced-motion: reduce)").matches:
    for index in range(5):
        _schedule(_spawn_bird, index * 450)
    interval_callback = _keep_callback(
        lambda: _spawn_bird() if Math.random() > 0.4 else None
    )
    window.setInterval(interval_callback, 3200)


def _on_mousemove(event):
    for card in document.querySelectorAll(".card"):
        rect = card.getBoundingClientRect()
        if (
            event.clientX < rect.left - 40
            or event.clientX > rect.right + 40
            or event.clientY < rect.top - 40
            or event.clientY > rect.bottom + 40
        ):
            continue

        px = (event.clientX - rect.left) / rect.width - 0.5
        py = (event.clientY - rect.top) / rect.height - 0.5
        card.style.transform = (
            f"perspective(700px) rotateX({py * -6}deg) "
            f"rotateY({px * 6}deg) translateY(-2px)"
        )


def _on_mouseleave(*_args):
    for card in document.querySelectorAll(".card"):
        card.style.transform = ""


_bind(document, "mousemove", _on_mousemove)
_bind(document, "mouseleave", _on_mouseleave)

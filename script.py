"""Browser-side Python behavior for the Supabase-powered bird catalog."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from catalog_data import create_catalog_data_client, format_availability
from js import Math, document, window  # pyright: ignore[reportMissingImports]
from pyodide.ffi import create_proxy  # pyright: ignore[reportMissingImports]


_callback_refs = []


@dataclass(frozen=True)
class Bird:
    id: str
    tag: str
    name: str
    sci: str | None
    family: str | None
    hatch: str | None
    life: str | None
    wing: str | None
    habitat: str | None
    diet: str | None
    status: str | None
    status_text: str | None
    call: str | None
    stat: str | None
    notes: str | None
    photo: str | None
    photo_alt: str | None


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
    element.addEventListener(event_name, _keep_callback(callback), capture)


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
    if not birds:
        if active_filter != "all" or search.value.strip():
            _show_message("No published birds match your filters.")
        else:
            _show_message("No birds are currently approved and published.")
        return

    _show_message("")
    for index, bird in enumerate(birds):
        card = document.createElement("div")
        card.className = "card"
        card.dataset.specimenId = bird.id
        card.style.animationDelay = f"{index * 0.06}s"

        specimen = document.createElement("div")
        specimen.className = "specimen-no"
        specimen.appendChild(
            _text_element("span", "", f"SPECIMEN NO. {index + 1:02d}")
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
chips = document.getElementById("chips")
scrim = document.getElementById("scrim")
d_name = document.getElementById("dName")
d_sci = document.getElementById("dSci")
d_photo = document.getElementById("dPhoto")
d_fields = document.getElementById("dFields")
d_notes = document.getElementById("dNotes")
stamp = document.getElementById("stamp")
catalog_message = document.getElementById("catalogMessage")
birds: list[Bird] = []
active_filter = "all"


def _show_message(message):
    catalog_message.textContent = message
    catalog_message.hidden = not bool(message)


def _render_chips(categories):
    chips.replaceChildren()
    all_chip = document.createElement("button")
    all_chip.className = "chip active"
    all_chip.dataset.f = "all"
    all_chip.textContent = "All"
    chips.appendChild(all_chip)

    for category in categories:
        chip = document.createElement("button")
        chip.className = "chip"
        chip.dataset.f = category
        chip.textContent = category.replace("_", " ").title()
        chips.appendChild(chip)


def _apply_filters(*_args):
    query = search.value.strip().casefold()
    matching_birds = []
    for bird in birds:
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
    if status and status.casefold() == "lc":
        return "status-lc"
    if status and status.casefold() == "nt":
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
    bird = next((item for item in birds if item.id == card.dataset.specimenId), None)
    if bird is not None:
        _open_dossier(bird)


def _on_chip_click(event):
    global active_filter
    selected_chip = event.target.closest(".chip")
    if selected_chip is None:
        return
    for chip in chips.querySelectorAll(".chip"):
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


def _bird_from_record(record: dict[str, Any], photo_url: str | None) -> Bird:
    category = record.get("category") or "uncategorized"
    status = record.get("iucn_status")
    checked_at = record.get("iucn_checked_at")
    status_text = None
    if checked_at:
        status_text = (
            f"{str(status).upper()} · checked {checked_at}"
            if status
            else f"Status not yet verified · last checked {checked_at}"
        )
    else:
        status_text = (
            f"{str(status).upper()} · Status not yet verified"
            if status
            else "Status not yet verified"
        )

    availability = record.get("availability")
    quantity = record.get("quantity_available")
    stat = (
        format_availability(availability, quantity)
        if availability
        else None
    )
    source_note = record.get("source_note")
    field_notes = record.get("field_notes")
    notes = " ".join(value for value in (source_note, field_notes) if value) or None
    bird_id = record.get("id")
    common_name = record.get("common_name")
    if not isinstance(bird_id, str) or not isinstance(common_name, str) or not common_name:
        raise ValueError("Published bird record is missing its ID or common name.")

    return Bird(
        id=bird_id,
        tag=str(category),
        name=common_name,
        sci=record.get("scientific_name"),
        family=record.get("family"),
        hatch=record.get("hatch_info"),
        life=record.get("lifespan"),
        wing=record.get("wingspan"),
        habitat=record.get("habitat"),
        diet=record.get("diet"),
        status=status,
        status_text=status_text,
        call=record.get("call"),
        stat=stat,
        notes=notes,
        photo=photo_url,
        photo_alt=record.get("photo_alt"),
    )


async def _load_catalog():
    global birds

    url_meta = document.querySelector('meta[name="supabase-url"]')
    key_meta = document.querySelector('meta[name="supabase-publishable-key"]')
    project_url = url_meta.content.strip() if url_meta is not None else ""
    publishable_key = key_meta.content.strip() if key_meta is not None else ""
    if not project_url or not publishable_key:
        _show_message(
            "Catalog configuration is missing. Add your Supabase project URL "
            "and publishable key to index.html."
        )
        return

    _show_message("Loading published birds…")
    try:
        client = create_catalog_data_client(
            {"url": project_url, "publishableKey": publishable_key}
        )
        records = await client.list_published_birds()
        loaded_birds = []
        for record in records:
            photo_url = None
            if record.get("photo_path"):
                try:
                    signed_photo = await client.create_bird_photo_url(record)
                    photo_url = signed_photo.url
                except Exception as error:
                    window.console.error(
                        "Could not load a published bird photo.", error
                    )
            loaded_birds.append(_bird_from_record(record, photo_url))

        birds = loaded_birds
        categories = sorted({bird.tag for bird in birds})
        _render_chips(categories)
        _apply_filters()
    except Exception as error:
        window.console.error("Could not load the published bird catalog.", error)
        grid.replaceChildren()
        _show_message("Catalog unavailable. Please try again later.")


def _start_catalog_load():
    asyncio.ensure_future(_load_catalog())


_bind(search, "input", _apply_filters)
_bind(chips, "click", _on_chip_click)
_bind(grid, "click", _on_grid_click)
_bind(document.getElementById("closeBtn"), "click", _close_dossier)
_bind(scrim, "click", _on_scrim_click)
_bind(document, "keydown", _on_keydown)
_bind(document.body, "error", _on_photo_error, capture=True)
_show_message("Loading published birds…")
_schedule(_start_catalog_load, 0)


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

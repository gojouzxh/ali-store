"""Browser-side Supabase catalog client for the PyScript frontend."""

from __future__ import annotations

import asyncio
import json
import re
import time
import warnings
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode, urljoin, urlsplit, urlunsplit

from js import AbortController, Headers, Object, clearTimeout, fetch, window  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy  # type: ignore[import-not-found]


PUBLIC_BIRD_FIELDS = (
    "id",
    "common_name",
    "scientific_name",
    "family",
    "category",
    "hatch_info",
    "lifespan",
    "wingspan",
    "habitat",
    "diet",
    "iucn_status",
    "iucn_checked_at",
    "source_note",
    "call",
    "field_notes",
    "availability",
    "quantity_available",
    "photo_path",
    "photo_alt",
    "sort_order",
)
PHOTO_PATH_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{12}/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:jpg|jpeg|png|webp)$"
)
MIN_SIGNED_URL_TTL = 60
MAX_SIGNED_URL_TTL = 3600
SIGNED_URL_REFRESH_BUFFER = 60
REQUEST_TIMEOUT_MS = 10_000


@dataclass(frozen=True)
class SignedPhoto:
    url: str
    expires_at: float


def format_availability(
    availability: str, quantity_available: int | None = None
) -> str:
    """Format a customer-facing availability label."""
    if availability not in {"available", "reserved", "sold"}:
        raise TypeError("Availability must be available, reserved, or sold.")
    if quantity_available is not None and (
        isinstance(quantity_available, bool)
        or not isinstance(quantity_available, int)
        or quantity_available < 0
    ):
        raise TypeError(
            "Available quantity must be a non-negative integer or None."
        )

    if (availability == "available" and quantity_available == 0) or (
        availability == "sold"
        and quantity_available is not None
        and quantity_available > 0
    ):
        warnings.warn(
            "Bird availability and quantity conflict; staff review is needed.",
            stacklevel=2,
        )
        return "Ask us about availability"

    if availability == "available" and quantity_available is not None:
        return f"Available ({quantity_available})"
    return availability.capitalize()


def _read_config(config: Any) -> tuple[str, str]:
    if not isinstance(config, dict):
        raise TypeError("Pass a Supabase project URL and publishable key.")

    url = config.get("url")
    publishable_key = config.get("publishableKey")
    if (
        not isinstance(url, str)
        or not isinstance(publishable_key, str)
        or not url.strip()
        or not publishable_key.strip()
    ):
        raise TypeError("Supabase URL and publishable key are required.")

    try:
        parsed = urlsplit(url.strip())
        _ = parsed.port
    except ValueError as error:
        raise TypeError("Supabase project URL must be a valid absolute URL.") from error
    if not parsed.scheme or not parsed.hostname:
        raise TypeError("Supabase project URL must be a valid absolute URL.")

    is_localhost = parsed.hostname.lower() in {"localhost", "127.0.0.1", "[::1]"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
        raise TypeError(
            "Supabase project URL must use HTTPS outside localhost."
        )

    project_url = urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "")
    )
    return project_url, publishable_key.strip()


async def _request_json(url: str, options: Any, operation: str) -> Any:
    controller = AbortController.new()
    timed_out = False

    def abort_request() -> None:
        nonlocal timed_out
        timed_out = True
        controller.abort()

    timeout_proxy = create_proxy(abort_request)
    timer = window.setTimeout(timeout_proxy, REQUEST_TIMEOUT_MS)
    options.signal = controller.signal
    try:
        response = await fetch(url, options)
        if not response.ok:
            raise RuntimeError(
                f"Supabase {operation} failed ({response.status})."
            )
        body = await response.text()
        if not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Supabase {operation} returned invalid JSON."
            ) from error
    except Exception as error:
        if timed_out:
            raise RuntimeError(
                f"Supabase request timed out after {REQUEST_TIMEOUT_MS} ms."
            ) from error
        raise
    finally:
        clearTimeout(timer)
        timeout_proxy.destroy()


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    default_port = 443 if parsed.scheme == "https" else 80
    return parsed.scheme, (parsed.hostname or "").lower(), parsed.port or default_port


class CatalogDataClient:
    """Read published bird rows and request short-lived photo URLs."""

    def __init__(self, config: Any):
        self._project_url, self._publishable_key = _read_config(config)
        self._signed_url_cache: dict[
            tuple[str, int], SignedPhoto | asyncio.Task[SignedPhoto]
        ] = {}

    async def list_published_birds(self) -> list[dict[str, Any]]:
        query = urlencode(
            {
                "select": ",".join(PUBLIC_BIRD_FIELDS),
                "order": "sort_order.asc,common_name.asc",
            }
        )
        headers = Headers.new()
        headers.set("apikey", self._publishable_key)
        headers.set("Accept", "application/json")
        options = Object.new()
        options.method = "GET"
        options.headers = headers
        options.cache = "no-store"

        birds = await _request_json(
            f"{self._project_url}/rest/v1/birds_public?{query}",
            options,
            "published bird query",
        )
        if not isinstance(birds, list):
            raise RuntimeError(
                "Supabase published bird query did not return a list."
            )
        return birds

    async def create_bird_photo_url(
        self, bird: dict[str, Any], expires_in_seconds: int = 3600
    ) -> SignedPhoto:
        if not isinstance(bird, dict) or not isinstance(bird.get("id"), str):
            raise TypeError("A bird record with an ID is required for a photo URL.")

        photo_path = bird.get("photo_path")
        if (
            not isinstance(photo_path, str)
            or not PHOTO_PATH_PATTERN.fullmatch(photo_path)
            or photo_path.split("/", 1)[0] != bird["id"]
        ):
            raise TypeError(
                "Bird photo path is missing or does not match the bird ID."
            )
        if (
            isinstance(expires_in_seconds, bool)
            or not isinstance(expires_in_seconds, int)
            or not MIN_SIGNED_URL_TTL
            <= expires_in_seconds
            <= MAX_SIGNED_URL_TTL
        ):
            raise ValueError(
                "Signed URL expiry must be between "
                f"{MIN_SIGNED_URL_TTL} and {MAX_SIGNED_URL_TTL} seconds."
            )

        cache_key = (photo_path, expires_in_seconds)
        cached = self._signed_url_cache.get(cache_key)
        refresh_buffer = min(
            SIGNED_URL_REFRESH_BUFFER,
            max(10, expires_in_seconds * 0.1),
        )
        if isinstance(cached, SignedPhoto) and (
            cached.expires_at - time.time() > refresh_buffer
        ):
            return cached
        if isinstance(cached, asyncio.Task):
            return await cached

        task = asyncio.create_task(
            self._request_signed_photo(bird, expires_in_seconds)
        )
        self._signed_url_cache[cache_key] = task
        try:
            signed_photo = await task
        except Exception:
            if self._signed_url_cache.get(cache_key) is task:
                del self._signed_url_cache[cache_key]
            raise
        self._signed_url_cache[cache_key] = signed_photo
        return signed_photo

    async def _request_signed_photo(
        self, bird: dict[str, Any], expires_in_seconds: int
    ) -> SignedPhoto:
        encoded_path = "/".join(
            quote(segment, safe="") for segment in bird["photo_path"].split("/")
        )
        endpoint = (
            f"{self._project_url}/storage/v1/object/sign/"
            f"bird-photos/{encoded_path}"
        )
        headers = Headers.new()
        headers.set("apikey", self._publishable_key)
        headers.set("Content-Type", "application/json")
        headers.set("Accept", "application/json")
        options = Object.new()
        options.method = "POST"
        options.headers = headers
        options.body = json.dumps({"expiresIn": expires_in_seconds})
        options.cache = "no-store"
        request_started_at = time.time()

        data = await _request_json(
            endpoint, options, "signed photo URL request"
        )
        if not isinstance(data, dict) or not isinstance(
            data.get("signedURL"), str
        ) or not data["signedURL"]:
            raise RuntimeError(
                "Supabase signed photo URL response did not include signedURL."
            )

        returned_url = data["signedURL"]
        if returned_url.startswith("/storage/v1/"):
            signed_url = urljoin(self._project_url + "/", returned_url)
        elif returned_url.startswith("/object/"):
            signed_url = urljoin(
                self._project_url + "/", f"/storage/v1{returned_url}"
            )
        elif urlsplit(returned_url).scheme in {"http", "https"}:
            signed_url = returned_url
        else:
            signed_url = urljoin(
                self._project_url + "/storage/v1/",
                returned_url.lstrip("/"),
            )
        if _origin(signed_url) != _origin(self._project_url):
            raise RuntimeError(
                "Supabase signed photo URL returned an unexpected origin."
            )

        return SignedPhoto(
            url=signed_url,
            expires_at=request_started_at + expires_in_seconds,
        )


def create_catalog_data_client(config: Any) -> CatalogDataClient:
    return CatalogDataClient(config)

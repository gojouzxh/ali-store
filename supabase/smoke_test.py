"""Run destructive Supabase bird-catalog checks against a disposable project."""

from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

REQUEST_TIMEOUT_SECONDS = 10
PUBLIC_BIRD_FIELDS = {
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
}
REQUIRED_ENVIRONMENT = (
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_STAFF_EMAIL",
    "SUPABASE_STAFF_PASSWORD",
    "SUPABASE_NONSTAFF_EMAIL",
    "SUPABASE_NONSTAFF_PASSWORD",
)
PNG_DATA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/"
    "x8AAwMCAO+/VxkAAAAASUVORK5CYII="
)


@dataclass(frozen=True)
class Response:
    ok: bool
    status: int
    text: str


class SmokeTest:
    def __init__(self, project_url: str, publishable_key: str):
        self.project_url = project_url
        self.publishable_key = publishable_key
        self.outcomes: list[tuple[str, bool, str]] = []
        self.bird_ids: set[str] = set()
        self.photo_paths: set[str] = set()

    def record(self, name: str, passed: bool, detail: str = "") -> None:
        self.outcomes.append((name, passed, detail))
        result = "PASS" if passed else "FAIL"
        suffix = f" — {detail}" if detail else ""
        print(f"{result} {name}{suffix}")

    def api_request(
        self,
        path: str,
        *,
        token: str | None = None,
        method: str = "GET",
        body: object | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> Response:
        request_headers = {
            "apikey": self.publishable_key,
            "Accept": "application/json",
            **(headers or {}),
        }
        if token:
            request_headers["Authorization"] = f"Bearer {token}"

        request_body: bytes | None
        if isinstance(body, bytes):
            request_body = body
        elif isinstance(body, str):
            request_body = body.encode("utf-8")
        elif body is not None:
            request_headers.setdefault("Content-Type", "application/json")
            request_body = json.dumps(body).encode("utf-8")
        else:
            request_body = None

        request = Request(
            f"{self.project_url}{path}",
            data=request_body,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return Response(
                    200 <= response.status < 300,
                    response.status,
                    response.read().decode("utf-8", errors="replace"),
                )
        except HTTPError as error:
            return Response(
                200 <= error.code < 300,
                error.code,
                error.read().decode("utf-8", errors="replace"),
            )
        except (TimeoutError, URLError) as error:
            reason = getattr(error, "reason", None)
            if isinstance(error, TimeoutError) or isinstance(reason, TimeoutError):
                raise RuntimeError(
                    f"Request timed out after {round(timeout * 1000)} ms."
                ) from error
            raise RuntimeError(f"Request failed: {error}") from error

    def fetch_bytes(self, url: str) -> Response:
        request = Request(url, method="GET")
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                response.read()
                return Response(
                    200 <= response.status < 300, response.status, ""
                )
        except HTTPError as error:
            error.read()
            return Response(200 <= error.code < 300, error.code, "")
        except (TimeoutError, URLError) as error:
            reason = getattr(error, "reason", None)
            if isinstance(error, TimeoutError) or isinstance(reason, TimeoutError):
                raise RuntimeError(
                    f"Request timed out after {REQUEST_TIMEOUT_SECONDS * 1000} ms."
                ) from error
            raise RuntimeError(f"Request failed: {error}") from error

    @staticmethod
    def require_ok(response: Response, operation: str) -> Response:
        if not response.ok:
            raise RuntimeError(f"{operation} returned HTTP {response.status}.")
        return response

    @staticmethod
    def parse_json(text: str, operation: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"{operation} returned invalid JSON.") from error

    def sign_in(self, email: str, password: str) -> str:
        response = self.api_request(
            "/auth/v1/token?grant_type=password",
            method="POST",
            body={"email": email, "password": password},
        )
        self.require_ok(response, "Password sign-in")
        result = self.parse_json(response.text, "Password sign-in")
        if not isinstance(result.get("access_token"), str) or not result["access_token"]:
            raise RuntimeError("Password sign-in did not return an access token.")
        return result["access_token"]

    def get_user_id(self, token: str) -> str:
        response = self.api_request("/auth/v1/user", token=token)
        self.require_ok(response, "Read signed-in user")
        user = self.parse_json(response.text, "Read signed-in user")
        if not isinstance(user.get("id"), str):
            raise RuntimeError("Auth user response did not include a user ID.")
        return user["id"]

    def create_bird(
        self, staff_token: str, common_name: str, published: bool
    ) -> str:
        response = self.api_request(
            "/rest/v1/birds?select=id",
            token=staff_token,
            method="POST",
            headers={"Prefer": "return=representation"},
            body={
                "common_name": common_name,
                "scientific_name": "Testus avis",
                "family": "Testidae",
                "category": "tropical",
                "is_approved": published,
                "is_published": published,
            },
        )
        self.require_ok(response, "Staff bird insert")
        result = self.parse_json(response.text, "Staff bird insert")
        if not isinstance(result, list) or not result or not isinstance(
            result[0].get("id"), str
        ):
            raise RuntimeError("Staff bird insert did not return the new bird ID.")
        self.bird_ids.add(result[0]["id"])
        return result[0]["id"]

    def create_incomplete_draft(self, staff_token: str, common_name: str) -> str:
        response = self.api_request(
            "/rest/v1/birds?select=id",
            token=staff_token,
            method="POST",
            headers={"Prefer": "return=representation"},
            body={
                "common_name": common_name,
                "scientific_name": None,
                "family": None,
                "category": None,
                "iucn_status": None,
                "source_note": None,
                "field_notes": None,
                "availability": None,
                "photo_alt": None,
                "is_approved": False,
                "is_published": False,
            },
        )
        self.require_ok(response, "Staff incomplete draft insert")
        result = self.parse_json(response.text, "Staff incomplete draft insert")
        if not isinstance(result, list) or not result or not isinstance(
            result[0].get("id"), str
        ):
            raise RuntimeError(
                "Staff incomplete draft insert did not return the new bird ID."
            )
        self.bird_ids.add(result[0]["id"])
        return result[0]["id"]

    @staticmethod
    def object_path(bird_id: str) -> str:
        return f"{bird_id}/{uuid.uuid4()}.png"

    @staticmethod
    def encoded_path(path: str) -> str:
        return "/".join(quote(segment, safe="") for segment in path.split("/"))

    def upload_photo(self, path: str, token: str | None) -> Response:
        return self.api_request(
            f"/storage/v1/object/bird-photos/{self.encoded_path(path)}",
            token=token,
            method="POST",
            headers={"Content-Type": "image/png", "x-upsert": "false"},
            body=PNG_DATA,
            timeout=60,
        )

    def set_photo_path(
        self, bird_id: str, photo_path: str | None, staff_token: str
    ) -> Response:
        return self.api_request(
            f"/rest/v1/birds?id=eq.{quote(bird_id, safe='')}",
            token=staff_token,
            method="PATCH",
            headers={"Prefer": "return=minimal"},
            body={"photo_path": photo_path},
        )

    def signed_photo_url(self, photo_path: str) -> str:
        response = self.api_request(
            f"/storage/v1/object/sign/bird-photos/"
            f"{self.encoded_path(photo_path)}",
            method="POST",
            body={"expiresIn": 300},
        )
        self.require_ok(response, "Create signed photo URL")
        result = self.parse_json(response.text, "Create signed photo URL")
        if not isinstance(result.get("signedURL"), str) or not result["signedURL"]:
            raise RuntimeError("Signed URL response did not contain signedURL.")

        returned_url = result["signedURL"]
        if returned_url.startswith("/storage/v1/"):
            url = urljoin(self.project_url + "/", returned_url)
        elif returned_url.startswith("/object/"):
            url = urljoin(self.project_url + "/", f"/storage/v1{returned_url}")
        elif urlsplit(returned_url).scheme in {"http", "https"}:
            url = returned_url
        else:
            url = urljoin(
                self.project_url + "/storage/v1/", returned_url.lstrip("/")
            )
        if self.origin(url) != self.origin(self.project_url):
            raise RuntimeError("Signed photo URL returned an unexpected origin.")
        return url

    @staticmethod
    def origin(url: str) -> tuple[str, str, int]:
        parsed = urlsplit(url)
        return (
            parsed.scheme,
            (parsed.hostname or "").lower(),
            parsed.port or (443 if parsed.scheme == "https" else 80),
        )

    def must_be_denied(
        self,
        response: Response,
        operation: str,
        expected_codes: tuple[str, ...] = (),
    ) -> None:
        if response.ok:
            raise RuntimeError(
                f"{operation} unexpectedly succeeded (HTTP {response.status})."
            )
        if response.status >= 500 or response.status in {408, 429}:
            raise RuntimeError(
                f"{operation} was inconclusive (HTTP {response.status})."
            )
        if expected_codes:
            try:
                code = self.parse_json(response.text, operation).get("code")
            except (RuntimeError, AttributeError):
                code = None
            if code not in expected_codes:
                raise RuntimeError(
                    f"{operation} was denied for an unexpected reason "
                    f"(HTTP {response.status}, code {code or 'none'})."
                )

    def must_be_allowed(self, response: Response, operation: str) -> None:
        self.require_ok(response, operation)

    def must_affect_no_rows(self, response: Response, operation: str) -> None:
        if not response.ok:
            self.must_be_denied(response, operation, ("42501",))
            return
        rows = self.parse_json(response.text, operation)
        if not isinstance(rows, list) or rows:
            count = len(rows) if isinstance(rows, list) else "an unknown number of"
            raise RuntimeError(f"{operation} changed {count} row(s).")

    def remove_photo(self, path: str, staff_token: str) -> None:
        response = self.api_request(
            "/storage/v1/object/bird-photos",
            token=staff_token,
            method="DELETE",
            body={"prefixes": [path]},
        )
        if not response.ok:
            raise RuntimeError(f"Photo cleanup returned HTTP {response.status}.")

    def remove_bird(self, bird_id: str, staff_token: str) -> None:
        response = self.api_request(
            f"/rest/v1/birds?id=eq.{quote(bird_id, safe='')}",
            token=staff_token,
            method="DELETE",
        )
        if not response.ok:
            raise RuntimeError(f"Bird cleanup returned HTTP {response.status}.")

    def run_check(self, name: str, action) -> None:
        try:
            action()
            self.record(name, True)
        except Exception as error:
            self.record(name, False, str(error))

    def run_access_checks(
        self,
        *,
        staff_token: str,
        nonstaff_token: str,
        nonstaff_user_id: str,
        published_bird_id: str,
        unpublished_bird_id: str,
        incomplete_bird_id: str,
        published_bird_name: str,
        unpublished_bird_name: str,
        incomplete_bird_name: str,
        published_photo_path: str,
        unpublished_photo_path: str,
    ) -> None:
        selected_ids = f"({published_bird_id},{unpublished_bird_id})"
        view_query = urlencode(
            {"select": "*", "id": f"in.{selected_ids}"}
        )

        def check_public_view() -> None:
            response = self.api_request(f"/rest/v1/birds_public?{view_query}")
            self.require_ok(response, "Anonymous birds_public query")
            rows = self.parse_json(response.text, "Anonymous birds_public query")
            if (
                not isinstance(rows, list)
                or len(rows) != 1
                or rows[0].get("id") != published_bird_id
            ):
                raise RuntimeError(
                    "Expected only the approved, published test bird from birds_public."
                )
            row = rows[0]
            if "is_approved" in row or "is_published" in row:
                raise RuntimeError(
                    "The public view exposed publication-control columns."
                )
            if set(row) - PUBLIC_BIRD_FIELDS:
                raise RuntimeError(
                    "The public view exposed a field outside the approved catalog list."
                )
            if PUBLIC_BIRD_FIELDS - set(row):
                raise RuntimeError(
                    "The public view is missing an expected catalog field."
                )

        self.run_check(
            "Anonymous public view is filtered and column-safe", check_public_view
        )

        def check_anonymous_direct_table() -> None:
            response = self.api_request(
                f"/rest/v1/birds?select=*&id=eq.{quote(published_bird_id, safe='')}"
            )
            self.must_be_denied(
                response, "Anonymous direct birds-table query", ("42501",)
            )

        self.run_check(
            "Anonymous direct birds-table access is denied",
            check_anonymous_direct_table,
        )

        def check_staff_helper() -> None:
            for role, token, expected in (
                ("anonymous", None, False),
                ("non-staff", nonstaff_token, False),
                ("staff", staff_token, True),
            ):
                response = self.api_request(
                    "/rest/v1/rpc/is_aviary_staff",
                    token=token,
                    method="POST",
                    body={},
                )
                self.require_ok(response, f"{role} staff-helper RPC")
                if self.parse_json(response.text, f"{role} staff-helper RPC") is not expected:
                    raise RuntimeError(
                        f"{role} staff-helper RPC returned the wrong result."
                    )

            read_response = self.api_request(
                "/rest/v1/staff_users?select=user_id", token=nonstaff_token
            )
            self.must_be_denied(
                read_response, "Non-staff read staff allow-list", ("42501",)
            )
            insert_response = self.api_request(
                "/rest/v1/staff_users",
                token=nonstaff_token,
                method="POST",
                body={"user_id": nonstaff_user_id},
            )
            self.must_be_denied(
                insert_response, "Non-staff self-promotion insert", ("42501",)
            )

        self.run_check(
            "Staff helper and staff allow-list protections", check_staff_helper
        )

        def check_photo_authorization() -> None:
            published_url = self.signed_photo_url(published_photo_path)
            self.require_ok(
                self.fetch_bytes(published_url), "Fetch published signed photo"
            )
            response = self.api_request(
                "/storage/v1/object/sign/bird-photos/"
                f"{self.encoded_path(unpublished_photo_path)}",
                method="POST",
                body={"expiresIn": 300},
            )
            self.must_be_denied(response, "Anonymous sign unpublished photo")

        self.run_check(
            "Anonymous published and unpublished photo authorization",
            check_photo_authorization,
        )

        def check_storage_listing() -> None:
            published_response = self.api_request(
                "/storage/v1/object/list/bird-photos",
                method="POST",
                body={"prefix": published_bird_id, "limit": 100, "offset": 0},
            )
            self.require_ok(published_response, "List published bird photo folder")
            published_items = self.parse_json(
                published_response.text, "List published bird photo folder"
            )
            published_filename = published_photo_path.split("/", 1)[1]
            if not isinstance(published_items, list) or not any(
                item.get("name") == published_filename for item in published_items
            ):
                raise RuntimeError(
                    "Published photo was not visible in the anonymous folder listing."
                )

            unpublished_response = self.api_request(
                "/storage/v1/object/list/bird-photos",
                method="POST",
                body={"prefix": unpublished_bird_id, "limit": 100, "offset": 0},
            )
            if not unpublished_response.ok:
                self.must_be_denied(
                    unpublished_response, "List unpublished bird photo folder"
                )
                return
            unpublished_items = self.parse_json(
                unpublished_response.text, "List unpublished bird photo folder"
            )
            if not isinstance(unpublished_items, list) or unpublished_items:
                raise RuntimeError(
                    "Anonymous listing exposed files from an unpublished bird folder."
                )

        self.run_check(
            "Anonymous Storage listing filters unpublished photos",
            check_storage_listing,
        )

        def check_nonstaff_rows() -> None:
            response = self.api_request(
                f"/rest/v1/birds?select=id,is_approved,is_published&id=in.{selected_ids}",
                token=nonstaff_token,
            )
            self.require_ok(response, "Non-staff birds query")
            rows = self.parse_json(response.text, "Non-staff birds query")
            if not isinstance(rows, list) or any(
                row.get("id") != published_bird_id
                or not row.get("is_approved")
                or not row.get("is_published")
                for row in rows
            ):
                raise RuntimeError("Non-staff query exposed an unpublished test row.")

        self.run_check("Non-staff sees published rows only", check_nonstaff_rows)

        def check_nonstaff_photo_signing() -> None:
            response = self.api_request(
                "/storage/v1/object/sign/bird-photos/"
                f"{self.encoded_path(unpublished_photo_path)}",
                token=nonstaff_token,
                method="POST",
                body={"expiresIn": 300},
            )
            self.must_be_denied(response, "Non-staff sign unpublished photo")

        self.run_check(
            "Non-staff cannot sign unpublished photo", check_nonstaff_photo_signing
        )

        def check_unauthorized_writes() -> None:
            row = {
                "common_name": f"Unauthorized smoke row {uuid.uuid4()}",
                "scientific_name": "Testus nonavis",
                "family": "Testidae",
                "category": "tropical",
            }
            for role, token in (
                ("anonymous", None),
                ("non-staff", nonstaff_token),
            ):
                insert_response = self.api_request(
                    "/rest/v1/birds",
                    token=token,
                    method="POST",
                    headers={"Prefer": "return=representation"},
                    body=row,
                )
                if insert_response.ok:
                    inserted_rows = self.parse_json(
                        insert_response.text, f"{role} bird insert"
                    )
                    for inserted in inserted_rows:
                        if isinstance(inserted.get("id"), str):
                            self.bird_ids.add(inserted["id"])
                self.must_be_denied(
                    insert_response, f"{role} insert bird", ("42501",)
                )

                upload_path = self.object_path(published_bird_id)
                upload_response = self.upload_photo(upload_path, token)
                if upload_response.ok:
                    self.photo_paths.add(upload_path)
                self.must_be_denied(upload_response, f"{role} upload photo")

        self.run_check(
            "Anonymous and non-staff cannot write birds or upload photos",
            check_unauthorized_writes,
        )

        def check_mutations() -> None:
            anon_patch = self.api_request(
                f"/rest/v1/birds?id=eq.{quote(published_bird_id, safe='')}",
                method="PATCH",
                headers={"Prefer": "return=representation"},
                body={"common_name": f"Unauthorized update {uuid.uuid4()}"},
            )
            self.must_be_denied(anon_patch, "Anonymous update bird", ("42501",))

            anon_delete = self.api_request(
                f"/rest/v1/birds?id=eq.{quote(unpublished_bird_id, safe='')}",
                method="DELETE",
                headers={"Prefer": "return=representation"},
            )
            self.must_be_denied(anon_delete, "Anonymous delete bird", ("42501",))

            nonstaff_patch = self.api_request(
                f"/rest/v1/birds?id=eq.{quote(published_bird_id, safe='')}",
                token=nonstaff_token,
                method="PATCH",
                headers={"Prefer": "return=representation"},
                body={"common_name": f"Unauthorized update {uuid.uuid4()}"},
            )
            self.must_affect_no_rows(nonstaff_patch, "Non-staff update bird")

            nonstaff_delete = self.api_request(
                f"/rest/v1/birds?id=eq.{quote(unpublished_bird_id, safe='')}",
                token=nonstaff_token,
                method="DELETE",
                headers={"Prefer": "return=representation"},
            )
            self.must_affect_no_rows(nonstaff_delete, "Non-staff delete bird")

            staff_read = self.api_request(
                "/rest/v1/birds?select=id,common_name,is_approved,is_published"
                f"&id=in.{selected_ids}",
                token=staff_token,
            )
            self.require_ok(staff_read, "Staff verify unauthorized bird mutations")
            rows = self.parse_json(
                staff_read.text, "Staff verify unauthorized bird mutations"
            )
            published = next(
                (row for row in rows if row.get("id") == published_bird_id), None
            )
            unpublished = next(
                (row for row in rows if row.get("id") == unpublished_bird_id), None
            )
            if (
                len(rows) != 2
                or published is None
                or published.get("common_name") != published_bird_name
                or not published.get("is_approved")
                or not published.get("is_published")
                or unpublished is None
                or unpublished.get("common_name") != unpublished_bird_name
                or unpublished.get("is_approved")
                or unpublished.get("is_published")
            ):
                raise RuntimeError(
                    "An unauthorized mutation changed or removed a test bird."
                )

        self.run_check(
            "Unauthorized updates and deletes do not change or remove birds",
            check_mutations,
        )

        def check_publication_constraints() -> None:
            publication_response = self.api_request(
                f"/rest/v1/birds?id=eq.{quote(unpublished_bird_id, safe='')}",
                token=staff_token,
                method="PATCH",
                headers={"Prefer": "return=minimal"},
                body={"is_published": True},
            )
            self.must_be_denied(
                publication_response, "Publish an unapproved test bird", ("23514",)
            )

            incomplete_publication = self.api_request(
                f"/rest/v1/birds?id=eq.{quote(incomplete_bird_id, safe='')}",
                token=staff_token,
                method="PATCH",
                headers={"Prefer": "return=minimal"},
                body={"is_approved": True, "is_published": True},
            )
            self.must_be_denied(
                incomplete_publication, "Publish an incomplete bird", ("23514",)
            )

            blank_scientific_response = self.api_request(
                "/rest/v1/birds?select=id",
                token=staff_token,
                method="POST",
                headers={"Prefer": "return=representation"},
                body={
                    "common_name": f"Smoke Test Blank Scientific Name {uuid.uuid4()}",
                    "scientific_name": "",
                    "family": "Testidae",
                    "category": "tropical",
                    "hatch_info": "Test hatch information",
                    "lifespan": "Test lifespan",
                    "wingspan": "Test wingspan",
                    "habitat": "Test habitat",
                    "diet": "Test diet",
                    "iucn_status": "NE",
                    "iucn_checked_at": "2025-01-01",
                    "source_note": "Smoke-test source",
                    "call": "Smoke-test call",
                    "field_notes": "Smoke-test field notes",
                    "availability": "sold",
                    "quantity_available": 0,
                    "photo_path": None,
                    "photo_alt": "Smoke-test photo description",
                    "is_approved": True,
                    "is_published": True,
                    "sort_order": 9999,
                },
            )
            if blank_scientific_response.ok:
                inserted_rows = self.parse_json(
                    blank_scientific_response.text,
                    "Insert published bird with blank scientific name",
                )
                if isinstance(inserted_rows, list):
                    for inserted in inserted_rows:
                        if isinstance(inserted.get("id"), str):
                            self.bird_ids.add(inserted["id"])
            self.must_be_denied(
                blank_scientific_response,
                "Insert published bird with blank scientific name",
                ("23514",),
            )

            incomplete_read = self.api_request(
                "/rest/v1/birds?select=common_name,is_approved,is_published"
                f"&id=eq.{quote(incomplete_bird_id, safe='')}",
                token=staff_token,
            )
            self.require_ok(incomplete_read, "Staff verify incomplete bird remains a draft")
            incomplete_rows = self.parse_json(
                incomplete_read.text, "Staff verify incomplete bird remains a draft"
            )
            if (
                len(incomplete_rows) != 1
                or incomplete_rows[0].get("common_name") != incomplete_bird_name
                or incomplete_rows[0].get("is_approved")
                or incomplete_rows[0].get("is_published")
            ):
                raise RuntimeError(
                    "The incomplete bird changed after its publication was rejected."
                )

            wrong_path = self.set_photo_path(
                unpublished_bird_id,
                f"{published_bird_id}/wrong-bird.png",
                staff_token,
            )
            self.must_be_denied(
                wrong_path, "Assign another bird photo folder", ("23514",)
            )
            self.require_ok(
                self.set_photo_path(unpublished_bird_id, None, staff_token),
                "Clear optional photo_path",
            )
            self.require_ok(
                self.set_photo_path(
                    unpublished_bird_id, unpublished_photo_path, staff_token
                ),
                "Restore unpublished test photo path",
            )

        self.run_check(
            "Staff publication and photo-path constraints",
            check_publication_constraints,
        )

        def check_upload_constraints() -> None:
            malformed_paths = (
                "photo.png",
                f"not-a-uuid/{uuid.uuid4()}.png",
            )
            for malformed_path in malformed_paths:
                response = self.upload_photo(malformed_path, staff_token)
                if response.ok:
                    self.photo_paths.add(malformed_path)
                self.must_be_denied(response, "Upload malformed photo path")

            uppercase_path = f"{published_bird_id}/UPPERCASE.JPG"
            malformed = self.upload_photo(uppercase_path, staff_token)
            if malformed.ok:
                self.photo_paths.add(uppercase_path)
            self.must_be_denied(malformed, "Upload uppercase-extension photo")

            nonexistent_path = f"{uuid.uuid4()}/{uuid.uuid4()}.png"
            nonexistent = self.upload_photo(nonexistent_path, staff_token)
            if nonexistent.ok:
                self.photo_paths.add(nonexistent_path)
            self.must_be_denied(nonexistent, "Upload photo for nonexistent bird")

            gif_path = self.object_path(published_bird_id)
            gif = self.api_request(
                "/storage/v1/object/bird-photos/"
                f"{self.encoded_path(gif_path)}",
                token=staff_token,
                method="POST",
                headers={"Content-Type": "image/gif", "x-upsert": "false"},
                body=b"GIF89a",
            )
            if gif.ok:
                self.photo_paths.add(gif_path)
            self.must_be_denied(gif, "Upload GIF photo")

            oversized_path = self.object_path(published_bird_id)
            oversized = self.api_request(
                "/storage/v1/object/bird-photos/"
                f"{self.encoded_path(oversized_path)}",
                token=staff_token,
                method="POST",
                headers={"Content-Type": "image/png", "x-upsert": "false"},
                body=bytes(6 * 1024 * 1024),
                timeout=60,
            )
            if oversized.ok:
                self.photo_paths.add(oversized_path)
            self.must_be_denied(oversized, "Upload 6 MB photo")

        self.run_check(
            "Staff uploads reject malformed, nonexistent, oversized and GIF objects",
            check_upload_constraints,
        )

    def run(self) -> bool:
        environment = os.environ
        missing = [name for name in REQUIRED_ENVIRONMENT if not environment.get(name)]
        if missing:
            print(
                f"Missing required environment variables: {', '.join(missing)}",
                file=sys.stderr,
            )
            return False
        if environment.get("SUPABASE_SMOKE_TEST_ACK") != "I_HAVE_A_DISPOSABLE_PROJECT":
            print(
                "Refusing to run without "
                "SUPABASE_SMOKE_TEST_ACK=I_HAVE_A_DISPOSABLE_PROJECT. "
                "This script creates and deletes test birds and Storage objects.",
                file=sys.stderr,
            )
            return False

        staff_token = None
        nonstaff_token = None
        try:
            staff_token = self.sign_in(
                environment["SUPABASE_STAFF_EMAIL"],
                environment["SUPABASE_STAFF_PASSWORD"],
            )
            nonstaff_token = self.sign_in(
                environment["SUPABASE_NONSTAFF_EMAIL"],
                environment["SUPABASE_NONSTAFF_PASSWORD"],
            )
            nonstaff_user_id = self.get_user_id(nonstaff_token)
            self.record("Staff and non-staff sign-in", True)
        except Exception as error:
            self.record("Staff and non-staff sign-in", False, str(error))

        if staff_token and nonstaff_token:
            try:
                suffix = uuid.uuid4()
                published_name = f"Smoke Test Published {suffix}"
                unpublished_name = f"Smoke Test Unpublished {suffix}"
                incomplete_name = f"Smoke Test Incomplete {suffix}"
                published_id = self.create_bird(
                    staff_token, published_name, True
                )
                unpublished_id = self.create_bird(
                    staff_token, unpublished_name, False
                )
                incomplete_id = self.create_incomplete_draft(
                    staff_token, incomplete_name
                )

                published_photo_path = self.object_path(published_id)
                unpublished_photo_path = self.object_path(unpublished_id)
                self.photo_paths.update(
                    (published_photo_path, unpublished_photo_path)
                )
                self.must_be_allowed(
                    self.upload_photo(published_photo_path, staff_token),
                    "Staff upload of published test photo",
                )
                self.must_be_allowed(
                    self.upload_photo(unpublished_photo_path, staff_token),
                    "Staff upload of unpublished test photo",
                )
                self.must_be_allowed(
                    self.set_photo_path(
                        published_id, published_photo_path, staff_token
                    ),
                    "Attach published test photo",
                )
                self.must_be_allowed(
                    self.set_photo_path(
                        unpublished_id, unpublished_photo_path, staff_token
                    ),
                    "Attach unpublished test photo",
                )
                self.record("Seed disposable birds and photos", True)
            except Exception as error:
                self.record("Seed disposable birds and photos", False, str(error))
            else:
                self.run_access_checks(
                    staff_token=staff_token,
                    nonstaff_token=nonstaff_token,
                    nonstaff_user_id=nonstaff_user_id,
                    published_bird_id=published_id,
                    unpublished_bird_id=unpublished_id,
                    incomplete_bird_id=incomplete_id,
                    published_bird_name=published_name,
                    unpublished_bird_name=unpublished_name,
                    incomplete_bird_name=incomplete_name,
                    published_photo_path=published_photo_path,
                    unpublished_photo_path=unpublished_photo_path,
                )
        if staff_token:
            cleanup_errors = []
            for path in self.photo_paths:
                try:
                    self.remove_photo(path, staff_token)
                except Exception as error:
                    cleanup_errors.append(str(error))
            for bird_id in self.bird_ids:
                try:
                    self.remove_bird(bird_id, staff_token)
                except Exception as error:
                    cleanup_errors.append(str(error))
            detail = (
                " ".join(cleanup_errors)
                if cleanup_errors
                else "test birds and photos removed"
            )
            self.record(
                "Cleanup disposable test data", not cleanup_errors, detail
            )

        passed = sum(outcome[1] for outcome in self.outcomes)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        print(
            f"\nSmoke test finished at {timestamp}. "
            f"{passed}/{len(self.outcomes)} checks passed."
        )
        return bool(self.outcomes) and all(outcome[1] for outcome in self.outcomes)


def validate_configuration(project_url: str) -> str:
    try:
        parsed = urlsplit(project_url)
        _ = parsed.port
    except ValueError as error:
        raise ValueError("SUPABASE_URL must be a valid absolute URL.") from error
    if not parsed.scheme or not parsed.hostname:
        raise ValueError("SUPABASE_URL must be a valid absolute URL.")

    is_localhost = parsed.hostname.lower() in {"localhost", "127.0.0.1", "[::1]"}
    if (
        (parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost))
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "SUPABASE_URL must use HTTPS outside localhost and contain no "
            "credentials, query, or fragment."
        )
    return project_url.rstrip("/")


def main() -> int:
    missing = [
        name for name in REQUIRED_ENVIRONMENT if not os.environ.get(name)
    ]
    if missing:
        print(
            f"Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1
    if os.environ.get("SUPABASE_SMOKE_TEST_ACK") != "I_HAVE_A_DISPOSABLE_PROJECT":
        print(
            "Refusing to run without "
            "SUPABASE_SMOKE_TEST_ACK=I_HAVE_A_DISPOSABLE_PROJECT. "
            "This script creates and deletes test birds and Storage objects.",
            file=sys.stderr,
        )
        return 1

    project_url = os.environ.get("SUPABASE_URL", "")
    try:
        normalized_url = validate_configuration(project_url)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    smoke_test = SmokeTest(
        normalized_url, os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    )
    return 0 if smoke_test.run() else 1


if __name__ == "__main__":
    raise SystemExit(main())

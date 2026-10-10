# Supabase setup

The browser app must use only the Supabase project URL and its publishable
(formerly `anon`) key. Never place a `service_role` or secret key in frontend
files. The database policies below remain the security boundary; hiding buttons
in the app is not authorization.

## 1. Create and secure the project

1. Create a Supabase project and keep its database password and keys private.
2. In the Authentication settings, disable public sign-ups and anonymous
   sign-ins. Dashboard menu names can change; verify both settings in the
   current project UI.
3. Create staff Auth users yourself from the Supabase dashboard. Do not provide
   a public registration page.
4. Add the first and subsequent staff UUIDs to `public.staff_users` from the
   SQL Editor as the project owner, using the command below. Authenticated and
   anonymous application roles have no table privileges or write policies on
   this allow-list. Keep the SQL Editor/project-owner access restricted.
5. Review the project's authentication and email settings before granting
   accounts to staff.

## 2. Apply the database and storage migration

In a fresh project, run `supabase/migrations/001_initial_schema.sql` and then
`supabase/migrations/002_allow_incomplete_drafts.sql` in the Supabase SQL
Editor, in that order. The first migration creates:

- `birds`, with species-level availability, optional quantity, IUCN metadata,
  photo path, and approval/publication flags. Both flags default to `false`.
- `birds_public`, a filtered `security_definer` view exposing only approved
  and published catalog fields. Anonymous users can select from this view but
  have no table or column privileges on `birds`; the view filters publication
  state itself and omits internal columns. Its definer behavior is intentional:
  do not switch it to invoker, since anonymous callers have no access to the
  base table.
- `is_published_bird_folder(text)`, a narrowly scoped `security_definer`
  helper that lets the Storage read policy authorize photos for published
  birds without granting anonymous access to the `birds` table.
- `staff_users`, an allow-list used by database and Storage policies.
- The private `bird-photos` bucket. Only photos attached to approved and
  published records can be read by visitors; staff can read all photos.
  Uploads, updates, and deletes require an allow-listed staff account. Files
  are limited to JPEG, PNG, or WebP and 5 MB. The required object path is
  `<bird-uuid>/<random-filename>.<jpg|jpeg|png|webp>` using lowercase
  extensions. Photo MIME and size limits rely on the uploaded file's declared
  Content-Type and Storage enforcement; they are not a substitute for server-
  side image-content validation.
- Row Level Security policies. Anonymous catalog reads use the filtered view.
  Signed-in non-staff users can also read published rows directly from
  `birds`, but cannot edit records or photos. Only user IDs present in
  `staff_users` can write records or photos.
- A constraint preventing a record from being published unless it is approved.
- A photo-path constraint requiring any configured photo to be stored in the
  folder matching its bird row ID.

The second migration makes the designated catalog fields nullable for
unpublished drafts, requires those fields before publication, and requires
photo alt text whenever a photo path is set. It does not alter RLS, the public
view, helper functions, or Storage rules.

The migration is written for a fresh project and is not idempotent. If it
partly fails, do not blindly run it again; use a disposable project and reset
or recreate it before retrying.

The Supabase advisor may report `birds_public` as a security-definer view and
`staff_users` as RLS-enabled without policies. Both are intentional: the view
is filtered and exposes only public columns, while the allow-list is reachable
only through the vetted helper under its owner context.

When adding another table to the exposed `public` schema, explicitly enable
RLS and revoke default `anon`/`authenticated` grants unless public access is
deliberately designed and tested.

Creating a Supabase Auth account does not automatically grant staff access.
After creating each staff account, add its Auth user ID in the SQL Editor:

```sql
insert into public.staff_users (user_id)
values ('<AUTH_USER_UUID>');
```

Run this using the Supabase SQL Editor as the project owner, not from the
website or a staff user's client session. The table has RLS enabled, is not
forced, and has no application-role policies; table privileges are revoked
from `anon` and `authenticated`. Its `user_id` foreign key references
`auth.users(id)` with `ON DELETE CASCADE`. Remove staff access from the SQL
Editor by deleting that row.

## 3. Configure and verify the app

The frontend configuration needs the project URL and publishable key. Keep
these public values separate from server-only keys. Never commit a secret key.

`js/catalog-data.js` is an isolated browser data module for the planned public
catalog. It reads only safe fields from `birds_public` and can request short-
lived photo URLs. It sends the publishable key in the `apikey` header. It is
not yet connected to `index.html`; the hard-coded demonstration catalog still
remains in `js/script.js` and is not safe to publish. The real owner records
are kept separately in `supabase/seeds/real_owner_birds_unpublished.sql`.
Configure only the project URL and publishable key when the tested frontend
switch is ready.

The module also exports `formatAvailability(availability, quantityAvailable)`.
For example, `formatAvailability('available', 2)` returns `Available (2)`.
The schema deliberately does not enforce availability/count consistency until
the owner confirms the remaining semantics. To avoid presenting contradictory
data as valid, the formatter logs a console warning and returns the neutral
customer label `Ask us about availability` for `available` with quantity zero
or `sold` with a positive quantity. Flag those records for staff review in the
future admin screen. Reserved quantity remains unconstrained.
Signed photo URLs are cached in memory until shortly before expiry; refresh is
still needed after the cache entry approaches its expiry. Unpublishing a bird
does not revoke an already-issued signed URL; it remains usable until its
expiry, for up to the one-hour maximum.
Both catalog and signed-photo requests time out after 10 seconds and reject
with an error. When the public page is wired, handle that failure by showing
the generic "Catalog unavailable" message, never by rendering demo records.

The current `index.html` loads `js/script.js` as a classic script and does not
load the catalog module. The eventual Supabase integration must load the module
with `<script type="module">`; serve the site over HTTP during development
(for example `python -m http.server`) because browsers do not load ES modules
from a `file://` page.

When the page is connected, render all client/data values using `textContent`
or safe DOM construction, never interpolating them into `innerHTML`. On a
catalog request failure, show visitors a generic "Catalog unavailable" message
without exposing technical error details; never show the
demo array as a fallback.
In bird dossiers, if `iucn_checked_at` is null, show "Status not yet verified"
rather than a blank date. Resize and convert photos to WebP at about 1200 px
wide before upload to help limit image transfer size.

### Deployment gate

Do not deploy the current prototype publicly or print a QR code for it. The
existing frontend still contains hard-coded demonstration birds. In the same
change that connects the public catalog to Supabase, remove that hard-coded
array and do not add a fallback that renders it when configuration or database
requests fail. The public page must show only rows returned by the approved and
published query. Do not print the QR code until that change is deployed and
the client confirms the final URL.

The generated QR code points to `https://gojouzxh.github.io/ali-store/`.
If this address changes, every printed copy must be replaced.

## Real owner bird data (unpublished)

`supabase/seeds/real_owner_birds_unpublished.sql` records the nine real owner
entries exactly as supplied. It maps each hatch date to `hatch_info`, keeps the
specified wingspan text, preserves both pair labels in `common_name`, leaves
`quantity_available` null, and explicitly sets `is_approved` and
`is_published` to `false` for every row. No scientific names, families,
categories, conservation data, field notes, availability, quantities, or
photos have been inferred.

**Do not run this seed after migration 001 alone.** Migration 001 declares
`scientific_name`, `family`, `category`, `iucn_status`, `source_note`,
`field_notes`, `availability`, and `photo_alt` as `NOT NULL`. The supplied
owner data leaves those values null. First apply
`supabase/migrations/001_initial_schema.sql`, then apply the additive
`supabase/migrations/002_allow_incomplete_drafts.sql`, then run the seed once.
The second migration permits those fields to be null on drafts but requires
them before publication. `call` remains `NOT NULL` and is supplied for all
nine records. No existing CHECK constraints, RLS, view, helper function, or
Storage rule is changed. The seed application status is **Not run**.

Existing `birds` CHECK constraints remain compatible with nullable drafts:

- The category, IUCN status, and availability allow-list checks evaluate to
  NULL for a NULL value; PostgreSQL CHECK constraints accept TRUE or NULL, so
  these checks reject invalid non-NULL values but permit an unknown draft
  value.
- `quantity_available is null or quantity_available >= 0` explicitly permits
  NULL and still rejects negative quantities.
- `not is_published or is_approved` still requires approval for every
  published record. Its flag columns remain NOT NULL.
- `photo_path is null or split_part(photo_path, '/', 1) = id::text` still
  permits a missing photo path and checks that any supplied path belongs to
  its row.

The new checks require all publication fields to be present, require
`scientific_name` and `family` to be non-blank after trimming whitespace, and
require `photo_alt` whenever `photo_path` is set. The real-owner seed has
neither a photo path nor alt text, so it satisfies that photo check while
remaining a draft. The seed is not idempotent; run it only once in the
intended project.

All nine records have these fields null:

| Bird | Fields left null |
|---|---|
| 01 — Grey/White | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 02 — Pale Yellow Budgies | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 03 — Lutino Yellow | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 04 — Green Budgies | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 05 — Blue/Violet Budgie | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 06 — Yellow Lutino Budgie | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 07 — Yellow Lutino (Pair record) | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 08 — Blue (Pair record) | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |
| 09 — Blue Lovebirds | `scientific_name`, `family`, `category`, `iucn_status`, `iucn_checked_at`, `source_note`, `field_notes`, `availability`, `quantity_available`, `photo_path`, `photo_alt` |

The current filter categories are limited to `raptor`, `water`, and `tropical`.
No category can be assigned from the supplied data without inference, so the
category chips cannot filter these entries until the owner supplies categories.
The current dossier layout expects scientific name/family, a conservation
status, and field notes; it has not been adapted to these null values. Do not
wire the data to the page until null display behavior is designed. The existing
hard-coded demonstration array remains in `js/script.js` because this data-only
change does not edit frontend code; this is not a fallback for the database and
the prototype must remain undeployed.

Before launch, prepare data and then test with at least two identities:

1. Apply migrations 001 and 002, in order, in a fresh disposable Supabase
   project.
2. Create a staff Auth user in the dashboard and add its UUID to
   `staff_users`.
3. Run the real-owner seed once; migration 002 was already applied in step 1.
   For security checks, as staff also create disposable test birds (including
   one approved/published and one unpublished bird) with test photos in their
   ID folders.
4. Run the anonymous and non-staff checks below. The allow-listed staff setup
   and disposable test-data actions happen before checks 1 and 2.

- An anonymous visitor must see only rows where `is_approved` and
  `is_published` are both true, and must not be able to write rows or upload
  photos. They must not be able to read a photo attached to an unpublished
  record.
- A signed-in user not listed in `staff_users` can read published rows, but
  must not be able to edit rows or upload, update, or delete photos.
- An allow-listed staff user can manage bird records and photos. Public photo
  links should be signed URLs with a short expiry (for example, 1 hour),
  generated when a page loads for published records. Anyone holding a signed
  URL can use it until expiry; unpublishing does not invalidate existing URLs.
  Refresh expired URLs while the page remains open.

## Pre-launch security test checklist

These tests are **not run** until a Supabase project is configured and the
migrations are applied. Record actual results and evidence here; do not mark a
test passed based only on inspecting the policy SQL.

| Check | How to test | Expected result | Result / date |
|---|---|---|---|
| Migration and RLS | Apply migrations 001 and 002 in order in a test project. Run the SQL verification queries below in the SQL Editor. | RLS is enabled on both app tables and the expected table/storage policies exist. | Not run |
| Real owner data seed | Apply migration 001, then migration 002, then run `supabase/seeds/real_owner_birds_unpublished.sql` once. Query the inserted owner rows. | Exactly nine owner records are inserted with both publication flags false and the supplied unspecified fields still NULL. | Not run |
| Incomplete draft publication guard | As allow-listed staff, attempt to set both `is_approved=true` and `is_published=true` on an owner-data draft that still has NULL publication-required fields. | The update is rejected with PostgREST/PostgreSQL check-violation code `23514`; the row remains unapproved and unpublished. | Not run |
| Blank scientific name publication guard | As allow-listed staff, insert a row with `is_approved=true`, `is_published=true`, `scientific_name=''`, and all other publication fields populated. | The insert is rejected with check-violation code `23514`. | Not run |
| Complete record can publish | As allow-listed staff, create a row with `common_name`, `call`, and all publication-required fields populated; leave `photo_path` NULL or provide `photo_alt` with it. Set `is_approved=true` and `is_published=true`. | The insert/update succeeds, demonstrating complete data can still be published while the existing approval rule remains enforced. | Not run |
| 1. Anonymous visitor | Use only the project's URL and publishable key. Query `birds_public?select=*` and confirm it contains only safe, approved, published fields. Try direct `birds?select=*`, REST `POST`, `PATCH`, and `DELETE` against a test row; attempt a Storage upload and create signed URLs for both unpublished and published photos. List files in the bucket and test paths with no folder, a non-UUID folder, and a valid UUID for a nonexistent bird. | The view returns only safe fields; direct access to `birds` is denied with PostgREST code `42501`; hidden rows are absent; writes/uploads are denied; signed-URL creation is denied for unpublished photos and succeeds for published photos; listing exposes only published bird folders; malformed and nonexistent-bird paths are denied cleanly. | Not run |
| 2. Non-staff authenticated user | Create a second test Auth account from the Supabase dashboard (do not enable public sign-ups), do not add its UUID to `staff_users`, then repeat the read/write/photo checks with that account's access token. For PATCH/DELETE, request representation and verify either a permission error or an empty returned row list; then read as staff to confirm the test rows are unchanged and still exist. | It can read only published records, cannot insert or upload, and cannot change or delete any bird row. A zero-row successful PATCH/DELETE is expected under RLS, provided staff confirms the rows remain unchanged. It cannot sign URLs for unpublished photos. | Not run |
| 3. Public account creation disabled | First pass the smoke test to establish that the project URL and key work. Then follow “Verify public sign-up and anonymous sign-in settings” below, using an email address you control (not an `example.com` address). | Email sign-up returns Auth `error_code=signup_disabled`; anonymous sign-in returns `error_code=anonymous_provider_disabled`. Unexpected success is a failure and creates an Auth user that must be deleted. Inconclusive status, URL/key, or rate-limit results do not pass. | Not run |
| 4. Allow-listed staff | Create a staff Auth user in the dashboard, add its Auth UUID to `staff_users`, and sign in. Insert, edit, and delete a disposable bird row; upload, update, and delete a disposable photo under `<bird-uuid>/<random-filename>.<extension>`. Try setting `photo_path` to another bird's UUID folder and to `null`; try malformed uploads, a nonexistent bird UUID, uppercase `.JPG`, a 6 MB image, and a `.png` path with `image/gif` Content-Type; request a signed URL for a published test bird photo. | Staff operations succeed for valid bird paths; assigning another bird's folder is rejected with check violation `23514`, setting `photo_path` to null is accepted, and malformed paths, nonexistent bird IDs, uppercase extension, oversized image, and disallowed GIF MIME are rejected. The published photo can be retrieved with its signed URL. Deleting the `staff_users` row removes write access. | Not run |
| Availability formatter | Run the module's formatter with `available/2`, `available/0`, `sold/5`, and `reserved/5`. | Valid available quantity formats as `Available (2)`; both contradictory combinations return `Ask us about availability` and log a warning; reserved quantity remains `Reserved`. | Not run |
| Catalog request timeout | Stub the catalog and signed-photo endpoints so they remain pending past the 10-second timeout (or use a test timer). | Both calls reject on timeout; when wired to the page, visitors see the generic catalog-unavailable state and never demo data. | Not run |
| Public dossier behavior | After the catalog is connected, test a record with `iucn_checked_at=null` and another with a date; simulate a failed catalog request and load the page over HTTP as an ES module. | The undated record says `Status not yet verified`, dated values are displayed, module loading succeeds over HTTP, and request errors show the generic unavailable state with no demo fallback. | Not run |
| Publication guard | As allow-listed staff, insert or update a test row with `is_published=true` and `is_approved=false`. | Database rejects the row because the approval constraint is violated. | Not run |
| Staff helper and allow-list lock | Use the smoke test or run the RPC and REST checks below with anonymous, non-staff, and staff credentials. | `is_aviary_staff()` returns false/false/true for anonymous/non-staff/staff; non-staff `SELECT` and self-promotion `INSERT` on `staff_users` fail with PostgREST code `42501`. | Not run |

SQL verification queries:

```sql
select n.nspname as schema_name, c.relname as table_name, c.relrowsecurity as rls_enabled
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where (n.nspname = 'public' and c.relname in ('birds', 'staff_users'))
   or (n.nspname = 'storage' and c.relname = 'objects')
order by n.nspname, c.relname;

select schemaname, tablename, policyname, roles, cmd, qual, with_check
from pg_policies
where (schemaname = 'public' and tablename in ('birds', 'staff_users'))
   or (schemaname = 'storage' and tablename = 'objects')
order by schemaname, tablename, policyname;

select table_schema, table_name, column_name, privilege_type, grantee
from information_schema.column_privileges
where table_schema = 'public'
  and table_name = 'birds'
  and grantee in ('anon', 'authenticated')
order by grantee, column_name;

select grantee, privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name = 'birds_public'
  and grantee in ('anon', 'authenticated', 'PUBLIC');

select grantee, privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name = 'birds'
  and grantee in ('anon', 'PUBLIC');

select c.relname as table_name, c.relrowsecurity as rls_enabled,
       c.relforcerowsecurity as rls_forced
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relname in ('birds', 'staff_users');

select grantee, privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name = 'staff_users'
  and grantee in ('anon', 'authenticated', 'public');
```

Expected: there are no anonymous or PUBLIC table/column privileges on
`birds`; `birds_public` has SELECT for `anon` and `authenticated`, but not
`PUBLIC`; `staff_users` has RLS enabled and `rls_forced = false`, with no
application-role grants or policies. The function-owner query below should
report `postgres` for both security-definer helpers when the migration was
applied by the SQL Editor as project owner:

```sql
select p.proname as function_name, r.rolname as function_owner
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
join pg_roles r on r.oid = p.proowner
where n.nspname = 'public'
  and p.proname in ('is_aviary_staff', 'is_published_bird_folder')
order by p.proname;
```

Test the helper and allow-list privileges in separate SQL Editor executions.
For the expected permission failures, run each statement in its own transaction;
a failed statement aborts the current transaction.

```sql
-- Anonymous: expect false.
begin;
set local role anon;
select public.is_aviary_staff();
rollback;

-- Signed-in non-staff: expect false.
begin;
set local role authenticated;
set local request.jwt.claims = '{"sub":"<NON_STAFF_USER_UUID>","role":"authenticated"}';
select public.is_aviary_staff();
rollback;

-- Non-staff read: expect permission denied.
begin;
set local role authenticated;
set local request.jwt.claims = '{"sub":"<NON_STAFF_USER_UUID>","role":"authenticated"}';
select * from public.staff_users;
rollback;

-- Non-staff self-promotion: expect permission denied.
begin;
set local role authenticated;
set local request.jwt.claims = '{"sub":"<NON_STAFF_USER_UUID>","role":"authenticated"}';
insert into public.staff_users (user_id) values ('<NON_STAFF_USER_UUID>');
rollback;

-- Allow-listed staff: expect true.
begin;
set local role authenticated;
set local request.jwt.claims = '{"sub":"<STAFF_USER_UUID>","role":"authenticated"}';
select public.is_aviary_staff();
rollback;
```

The non-staff `SELECT` and `INSERT` statements should raise
`permission denied for table staff_users` because the roles lack table
privileges; they should not return an empty result or an RLS violation. The
helper's `SECURITY DEFINER` owner needs to bypass RLS on `staff_users`; do not
enable `FORCE ROW LEVEL SECURITY` on that table. Confirm its owner is
`postgres` using the catalog query above.

This prototype migration has not yet been applied to a live Supabase project.
Apply it in a test project first and run the authorization checks above before
using real client records.

### Optional automated smoke test

`supabase/smoke-test.mjs` uses only Node.js built-ins and requires Node 18 or
newer. Run it only against a disposable test project after both migrations:
it creates three temporary bird rows and two photos, verifies access with
staff, non-staff, and anonymous requests, then attempts to remove all created
rows and files. It refuses to
start unless `SUPABASE_SMOKE_TEST_ACK` is exactly
`I_HAVE_A_DISPOSABLE_PROJECT`.

Before running it:

1. Apply migrations 001 and 002 in order, then create a staff Auth user plus a separate
   non-staff Auth user in the dashboard. Enable **Auto Confirm User** for both
   accounts (or confirm them before the test), then add only the staff user's
   UUID to `staff_users`; keep public sign-ups and anonymous sign-ins disabled.
2. In PowerShell, set the non-password values directly, then prompt for the
   passwords as secure input so they are not echoed or stored in command
   history:

   ```powershell
   $env:SUPABASE_URL = "https://<project>.supabase.co"
   $env:SUPABASE_PUBLISHABLE_KEY = "<publishable key>"
   $env:SUPABASE_STAFF_EMAIL = "<staff email>"
   $env:SUPABASE_NONSTAFF_EMAIL = "<non-staff email>"
   $env:SUPABASE_SMOKE_TEST_ACK = "I_HAVE_A_DISPOSABLE_PROJECT"

   $securePassword = Read-Host "Staff password" -AsSecureString
   $passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
   try {
       $env:SUPABASE_STAFF_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
   } finally {
       [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
   }

   $securePassword = Read-Host "Non-staff password" -AsSecureString
   $passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
   try {
       $env:SUPABASE_NONSTAFF_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
   } finally {
       [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
   }
   ```

   Passwords remain in the current PowerShell process environment until you
   clear them or close that shell. Do not use shared terminals or paste them
   into logs. If you use a `.env` file instead, add it to `.gitignore`; Node's
   `--env-file` flag requires Node 20.6 or newer.
3. From the project folder, run `node .\supabase\smoke-test.mjs` in
   PowerShell. Do not put credentials in the script, a committed file, or
   shared logs; do not paste credentials into chat.

The script prints pass/fail results with a UTC timestamp and exits nonzero if
any check or cleanup fails. It does not test the dashboard's sign-up and
anonymous-sign-in toggles, because attempting account creation could leave
unwanted accounts behind; verify those settings and their API behavior
separately using the manual checklist above. It uses HTTP 60-second timeouts
for photo uploads, including the 6 MB negative test. It confirms that
non-staff PATCH/DELETE requests either fail with permission denied or affect
zero rows, then checks as staff that neither test bird changed or disappeared.
It expects PostgREST permission-denial code `42501` for table/allow-list
authorization and check-violation code `23514` for publication and photo-path
constraints; Storage denials are checked by failure status without assuming a
particular JSON error code. If cleanup fails or execution is interrupted,
remove any `Smoke Test` birds and their Storage files from the test project
before rerunning.

### Verify public sign-up and anonymous sign-in settings

The automated smoke test deliberately does not probe Auth account creation.
Run the smoke test successfully first to verify the project URL and key. Then,
after disabling both settings in the dashboard, run this PowerShell check with
the project URL and publishable key already set in the environment. The
expected Supabase Auth error codes are `signup_disabled` and
`anonymous_provider_disabled` (see [Supabase Auth error codes](https://supabase.com/docs/guides/auth/debugging/error-codes)).
The email sign-up test uses an address you control, so an unexpected account
creation can be confirmed and cleaned up. Do not use `example.com` or another
reserved test domain: Auth may reject it as an invalid address before the
sign-up setting is checked. The check prints status and error codes, never
response bodies or passwords:

```powershell
$headers = @{
    apikey = $env:SUPABASE_PUBLISHABLE_KEY
}

$signupEmail = Read-Host "Email address you control (a plus alias is suitable)"
$securePassword = Read-Host "Temporary signup-check password" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $signupPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
}

function Test-AuthRequestRejected($Label, $Body, $ExpectedCode, $CreatedAccountEmail = $null) {
    try {
        $result = Invoke-RestMethod -Method Post `
            -Uri "$env:SUPABASE_URL/auth/v1/signup" `
            -Headers $headers `
            -ContentType "application/json" `
            -Body $Body
        Write-Output "FAIL $Label - request succeeded; this setting is still enabled"
        if ($result.user.id) {
            Write-Output "CLEANUP delete auth user id: $($result.user.id)"
        }
        if ($CreatedAccountEmail) {
            Write-Output "CLEANUP account email: $CreatedAccountEmail"
        }
    } catch {
        $caughtError = $_
        $code = $null
        $errorBody = $caughtError.ErrorDetails.Message
        if ($errorBody) {
            $parsedError = ConvertFrom-Json -InputObject $errorBody -ErrorAction SilentlyContinue
            if ($null -ne $parsedError) {
                $code = $parsedError.error_code
            }
        }
        $response = $caughtError.Exception.Response
        if ($null -ne $response) {
            $status = [int]$response.StatusCode
            $statusText = "HTTP $status"
        } else {
            $status = $null
            $statusText = "no HTTP response"
        }

        if ($code -eq $ExpectedCode) {
            Write-Output "PASS $Label - $statusText ($code)"
        } else {
            if ($null -eq $response) {
                Write-Output "INCONCLUSIVE $Label - no HTTP response (check network and project URL)"
            } else {
                if ($status -ge 500 -or $status -eq 408 -or $status -eq 429 -or $status -eq 401 -or $status -eq 403 -or $status -eq 404) {
                    Write-Output "INCONCLUSIVE $Label - HTTP $status (check URL, key, or rate limit)"
                } else {
                    if ($code -eq "email_provider_disabled") {
                        Write-Output "CHECK $Label - HTTP $status, email_provider_disabled (password sign-in may also be disabled)"
                    } else {
                        Write-Output "CHECK $Label - HTTP $status, error_code '$code' (expected '$ExpectedCode'; sign-up gate not confirmed)"
                    }
                }
            }
        }
    }
}

$signupBody = @{
    email = $signupEmail
    password = $signupPassword
} | ConvertTo-Json -Compress
Test-AuthRequestRejected "Public email signup disabled" $signupBody `
    "signup_disabled" $signupEmail
Test-AuthRequestRejected "Anonymous sign-in disabled" "{}" `
    "anonymous_provider_disabled"

Remove-Variable signupPassword, signupBody, securePassword, passwordPointer `
    -ErrorAction SilentlyContinue
```

Use an address you control, preferably a plus alias that you can monitor.
`PASS` means the exact expected setting-specific error
code was returned. `FAIL` means the request succeeded and that setting remains
enabled; the output prints the created Auth user ID and/or email for cleanup.
This applies to anonymous sign-in too: a successful anonymous sign-in creates
an anonymous Auth user and session. Delete that Auth user in **Authentication >
Users** using the printed ID. `INCONCLUSIVE` means there was no response, a
server error, a likely URL/key error, or rate limiting; correct the setup or
wait and retry. `CHECK` means the request failed for a different Auth error
code, so the sign-up setting has not been confirmed. In particular,
`email_address_invalid` and `email_address_not_authorized` mean the request may
have been rejected before reaching the sign-up gate; they are not proof that
sign-ups are disabled. `email_provider_disabled` means the Email provider is
off, which may also break the staff accounts' password sign-in; enable the
Email provider and disable only its “allow new users to sign up” setting.
Other codes also need investigation before treating the check as confirmed.
The prompt avoids echoing the temporary password, but it is briefly held in
PowerShell process memory; close the shell after the check.

## Data model assumptions

- Each row is a **species listing**, with one availability status and an
  optional non-negative `quantity_available`. The owner confirmed the example
  behavior: for three birds of a species with one sold, show `Available (2)`.
  This does not track individual birds separately. The schema does not enforce
  a relationship between the count and the availability status; the owner has
  not confirmed how counts should be represented for reserved or sold listings.
  A null quantity means the count is not being shown.
  Quantity/status contradictions are not blocked in the database pending owner
  confirmation; the catalog formatter flags the two clearly contradictory
  combinations for staff review instead of displaying them as valid.
- `scientific_name` is the single field for the species' scientific name.
- Only client-confirmed species should be entered. New records remain hidden
  until both `is_approved` and `is_published` are explicitly set to `true`.
- `photo_path` stores a path inside the private Storage bucket, not a complete
  image URL. The path must be `<bird-uuid>/<random-filename>.<extension>`.
  The database requires its first path segment to match the row's own bird ID.
  The app must request a short-lived signed URL for published bird photos;
  do not use permanent public URLs. Use random, non-identifying filenames.
  Signed URLs can be used by anyone who obtains them until they expire.
  Upload paths must use lowercase file extensions; `.JPG` does not match the
  current Storage policy.
- IUCN status is entered manually. `iucn_checked_at` is the date checked and
  `source_note` records the source/reference. If the checked date is null, the
  dossier should say "Status not yet verified."
- Resize and convert photos to WebP at about 1200 px wide before upload to
  reduce image size and help control transfer usage.
- `service_role` and other secret keys must never be included in frontend code.

## Deferred until after the migration passes

- Do not add a `quantity_reserved` field, hide quantities above a threshold, or
  automatically change availability based on quantity. These behaviors have
  not been approved by the owner.
- Do not build quantity-changing admin actions until they use an atomic
  database operation. A read-then-write update can lose a sale if two staff
  members update at once. After applying and testing this migration, add and
  test a database function that decrements the quantity in one statement only
  when it is greater than zero, then have the admin call that function. Do not
  automatically change the availability status; the owner has not approved
  automatic status transitions or defined reserved/sold quantity semantics.
- In the frontend, call Supabase `createSignedUrl` only for published bird
  photos, retain the expiration time, and request a replacement when needed
  after expiry. A signed URL is usable by anyone who obtains it until it
  expires.
- Deleting a bird row does not automatically remove its Storage objects.
  Delete photo files through the Supabase Storage API or dashboard, never with
  direct SQL against `storage.objects`. Ensure admin deletion handles orphaned
  photos deliberately.

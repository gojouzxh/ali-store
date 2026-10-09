import { randomUUID } from 'node:crypto';

const REQUEST_TIMEOUT_MS = 10000;
const PUBLIC_BIRD_FIELDS = new Set([
  'id',
  'common_name',
  'scientific_name',
  'family',
  'category',
  'hatch_info',
  'lifespan',
  'wingspan',
  'habitat',
  'diet',
  'iucn_status',
  'iucn_checked_at',
  'source_note',
  'call',
  'field_notes',
  'availability',
  'quantity_available',
  'photo_path',
  'photo_alt',
  'sort_order'
]);
const requiredEnvironment = [
  'SUPABASE_URL',
  'SUPABASE_PUBLISHABLE_KEY',
  'SUPABASE_STAFF_EMAIL',
  'SUPABASE_STAFF_PASSWORD',
  'SUPABASE_NONSTAFF_EMAIL',
  'SUPABASE_NONSTAFF_PASSWORD'
];
const missingEnvironment = requiredEnvironment.filter(name => !process.env[name]);
const outcomes = [];
const birdIds = new Set();
const photoPaths = new Set();
const pngData = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/VxkAAAAASUVORK5CYII=',
  'base64'
);
const projectUrl = process.env.SUPABASE_URL?.replace(/\/+$/, '');
const publishableKey = process.env.SUPABASE_PUBLISHABLE_KEY;

function validateConfiguration() {
  let url;
  try {
    url = new URL(projectUrl);
  } catch {
    throw new Error('SUPABASE_URL must be a valid absolute URL.');
  }
  const isLocalhost = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((url.protocol !== 'https:' && !isLocalhost) ||
      url.username || url.password || url.search || url.hash) {
    throw new Error('SUPABASE_URL must use HTTPS outside localhost and contain no credentials, query, or fragment.');
  }
}

function record(name, passed, detail = '') {
  outcomes.push({ name, passed, detail });
  console.log(`${passed ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`);
}

function requireOk(response, operation) {
  if (!response.ok) {
    throw new Error(`${operation} returned HTTP ${response.status}.`);
  }
  return response;
}

function parseJson(text, operation) {
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${operation} returned invalid JSON.`);
  }
}

async function fetchBytesWithTimeout(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, { signal: controller.signal });
    await response.arrayBuffer();
    return { ok: response.ok, status: response.status };
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error(`Request timed out after ${REQUEST_TIMEOUT_MS} ms.`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function apiRequest(path, {
  token,
  method = 'GET',
  body,
  headers = {},
  timeoutMs = REQUEST_TIMEOUT_MS
} = {}) {
  const requestHeaders = {
    apikey: publishableKey,
    Accept: 'application/json',
    ...headers
  };
  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  let requestBody = body;
  if (body !== undefined && !Buffer.isBuffer(body) && typeof body !== 'string') {
    requestHeaders['Content-Type'] ??= 'application/json';
    requestBody = JSON.stringify(body);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${projectUrl}${path}`, {
      method,
      headers: requestHeaders,
      body: requestBody,
      signal: controller.signal
    });
    return {
      ok: response.ok,
      status: response.status,
      text: await response.text()
    };
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs} ms.`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function signIn(email, password) {
  const response = await apiRequest('/auth/v1/token?grant_type=password', {
    method: 'POST',
    body: { email, password }
  });
  requireOk(response, 'Password sign-in');
  const result = parseJson(response.text, 'Password sign-in');
  if (typeof result.access_token !== 'string' || !result.access_token) {
    throw new Error('Password sign-in did not return an access token.');
  }
  return result.access_token;
}

async function getUserId(token) {
  const response = await apiRequest('/auth/v1/user', { token });
  requireOk(response, 'Read signed-in user');
  const user = parseJson(response.text, 'Read signed-in user');
  if (typeof user.id !== 'string') {
    throw new Error('Auth user response did not include a user ID.');
  }
  return user.id;
}

async function createBird(staffToken, commonName, published) {
  const response = await apiRequest('/rest/v1/birds?select=id', {
    token: staffToken,
    method: 'POST',
    headers: { Prefer: 'return=representation' },
    body: {
      common_name: commonName,
      scientific_name: 'Testus avis',
      family: 'Testidae',
      category: 'tropical',
      is_approved: published,
      is_published: published
    }
  });
  requireOk(response, 'Staff bird insert');
  const result = parseJson(response.text, 'Staff bird insert');
  if (!Array.isArray(result) || typeof result[0]?.id !== 'string') {
    throw new Error('Staff bird insert did not return the new bird ID.');
  }
  birdIds.add(result[0].id);
  return result[0].id;
}

async function uploadPhoto(path, token) {
  return apiRequest(
    `/storage/v1/object/bird-photos/${path.split('/').map(encodeURIComponent).join('/')}`,
    {
      token,
      method: 'POST',
      headers: {
        'Content-Type': 'image/png',
        'x-upsert': 'false'
      },
      timeoutMs: 60000,
      body: pngData
    }
  );
}

async function setPhotoPath(birdId, photoPath, staffToken) {
  return apiRequest(`/rest/v1/birds?id=eq.${encodeURIComponent(birdId)}`, {
    token: staffToken,
    method: 'PATCH',
    headers: { Prefer: 'return=minimal' },
    body: { photo_path: photoPath }
  });
}

function objectPath(birdId) {
  return `${birdId}/${randomUUID()}.png`;
}

async function signedPhotoUrl(photoPath) {
  const response = await apiRequest(
    `/storage/v1/object/sign/bird-photos/${photoPath.split('/').map(encodeURIComponent).join('/')}`,
    { method: 'POST', body: { expiresIn: 300 } }
  );
  requireOk(response, 'Create signed photo URL');
  const result = parseJson(response.text, 'Create signed photo URL');
  if (typeof result.signedURL !== 'string' || !result.signedURL) {
    throw new Error('Signed URL response did not contain signedURL.');
  }

  let url;
  if (/^https?:\/\//i.test(result.signedURL)) {
    url = new URL(result.signedURL);
  } else if (result.signedURL.startsWith('/storage/v1/')) {
    url = new URL(result.signedURL, projectUrl);
  } else if (result.signedURL.startsWith('/object/')) {
    url = new URL(`/storage/v1${result.signedURL}`, projectUrl);
  } else {
    url = new URL(
      result.signedURL.replace(/^\/+/, ''),
      new URL('/storage/v1/', projectUrl)
    );
  }
  if (url.origin !== new URL(projectUrl).origin) {
    throw new Error('Signed photo URL returned an unexpected origin.');
  }
  return url;
}

function mustBeDenied(response, operation, expectedCodes = []) {
  if (response.ok) {
    throw new Error(`${operation} unexpectedly succeeded (HTTP ${response.status}).`);
  }
  if (response.status >= 500 || [408, 429].includes(response.status)) {
    throw new Error(`${operation} was inconclusive (HTTP ${response.status}).`);
  }
  if (expectedCodes.length) {
    let code;
    try {
      code = JSON.parse(response.text).code;
    } catch {
      code = undefined;
    }
    if (!expectedCodes.includes(code)) {
      throw new Error(
        `${operation} was denied for an unexpected reason ` +
        `(HTTP ${response.status}, code ${code ?? 'none'}).`
      );
    }
  }
}

function mustBeAllowed(response, operation) {
  requireOk(response, operation);
}

function mustAffectNoRows(response, operation) {
  if (!response.ok) {
    return mustBeDenied(response, operation, ['42501']);
  }
  const rows = parseJson(response.text, operation);
  if (!Array.isArray(rows) || rows.length !== 0) {
    throw new Error(
      `${operation} changed ${Array.isArray(rows) ? rows.length : 'an unknown number of'} row(s).`
    );
  }
}

async function removePhoto(path, staffToken) {
  const response = await apiRequest('/storage/v1/object/bird-photos', {
    token: staffToken,
    method: 'DELETE',
    body: { prefixes: [path] }
  });
  if (!response.ok) {
    throw new Error(`Photo cleanup returned HTTP ${response.status}.`);
  }
}

async function removeBird(birdId, staffToken) {
  const response = await apiRequest(
    `/rest/v1/birds?id=eq.${encodeURIComponent(birdId)}`,
    { token: staffToken, method: 'DELETE' }
  );
  if (!response.ok) {
    throw new Error(`Bird cleanup returned HTTP ${response.status}.`);
  }
}

async function run() {
  if (missingEnvironment.length) {
    console.error(`Missing required environment variables: ${missingEnvironment.join(', ')}`);
    return false;
  }
  if (process.env.SUPABASE_SMOKE_TEST_ACK !== 'I_HAVE_A_DISPOSABLE_PROJECT') {
    console.error(
      'Refusing to run without SUPABASE_SMOKE_TEST_ACK=I_HAVE_A_DISPOSABLE_PROJECT. ' +
      'This script creates and deletes test birds and Storage objects.'
    );
    return false;
  }
  try {
    validateConfiguration();
  } catch (error) {
    console.error(error.message);
    return false;
  }

  let staffToken;
  let nonStaffToken;
  let nonStaffUserId;
  let publishedBirdId;
  let unpublishedBirdId;
  let publishedBirdName;
  let unpublishedBirdName;
  let publishedPhotoPath;
  let unpublishedPhotoPath;
  let seedReady = false;

  const authReady = await (async () => {
    try {
      staffToken = await signIn(
        process.env.SUPABASE_STAFF_EMAIL,
        process.env.SUPABASE_STAFF_PASSWORD
      );
      nonStaffToken = await signIn(
        process.env.SUPABASE_NONSTAFF_EMAIL,
        process.env.SUPABASE_NONSTAFF_PASSWORD
      );
      nonStaffUserId = await getUserId(nonStaffToken);
      record('Staff and non-staff sign-in', true);
      return true;
    } catch (error) {
      record('Staff and non-staff sign-in', false, error.message);
      return false;
    }
  })();

  if (authReady) {
    try {
      const suffix = randomUUID();
      publishedBirdName = `Smoke Test Published ${suffix}`;
      unpublishedBirdName = `Smoke Test Unpublished ${suffix}`;
      publishedBirdId = await createBird(
        staffToken,
        publishedBirdName,
        true
      );
      unpublishedBirdId = await createBird(
        staffToken,
        unpublishedBirdName,
        false
      );

      publishedPhotoPath = objectPath(publishedBirdId);
      unpublishedPhotoPath = objectPath(unpublishedBirdId);
      photoPaths.add(publishedPhotoPath);
      photoPaths.add(unpublishedPhotoPath);
      const publishedUpload = await uploadPhoto(publishedPhotoPath, staffToken);
      mustBeAllowed(publishedUpload, 'Staff upload of published test photo');
      const unpublishedUpload = await uploadPhoto(unpublishedPhotoPath, staffToken);
      mustBeAllowed(unpublishedUpload, 'Staff upload of unpublished test photo');
      mustBeAllowed(
        await setPhotoPath(publishedBirdId, publishedPhotoPath, staffToken),
        'Attach published test photo'
      );
      mustBeAllowed(
        await setPhotoPath(unpublishedBirdId, unpublishedPhotoPath, staffToken),
        'Attach unpublished test photo'
      );
      record('Seed disposable birds and photos', true);
      seedReady = true;
    } catch (error) {
      record('Seed disposable birds and photos', false, error.message);
    }

    if (seedReady) {
      await runAccessChecks({
        staffToken,
        nonStaffToken,
        nonStaffUserId,
        publishedBirdId,
        unpublishedBirdId,
        publishedBirdName,
        unpublishedBirdName,
        publishedPhotoPath,
        unpublishedPhotoPath
      });
    }
  }

  if (staffToken) {
    const cleanupErrors = [];
    for (const path of photoPaths) {
      try {
        await removePhoto(path, staffToken);
      } catch (error) {
        cleanupErrors.push(error.message);
      }
    }
    for (const id of birdIds) {
      try {
        await removeBird(id, staffToken);
      } catch (error) {
        cleanupErrors.push(error.message);
      }
    }
    record(
      'Cleanup disposable test data',
      cleanupErrors.length === 0,
      cleanupErrors.length ? cleanupErrors.join(' ') : 'test birds and photos removed'
    );
  }

  console.log(`\nSmoke test finished at ${new Date().toISOString()}.`);
  console.log(`${outcomes.filter(item => item.passed).length}/${outcomes.length} checks passed.`);
  return outcomes.length > 0 && outcomes.every(item => item.passed);
}

async function runAccessChecks({
  staffToken,
  nonStaffToken,
  nonStaffUserId,
  publishedBirdId,
  unpublishedBirdId,
  publishedBirdName,
  unpublishedBirdName,
  publishedPhotoPath,
  unpublishedPhotoPath
}) {
  const runCheck = async (name, action) => {
    try {
      await action();
      record(name, true);
    } catch (error) {
      record(name, false, error.message);
    }
  };

  const selectedIds = `(${publishedBirdId},${unpublishedBirdId})`;
  const viewQuery = new URLSearchParams({
    select: '*',
    id: `in.${selectedIds}`
  });

  await runCheck('Anonymous public view is filtered and column-safe', async () => {
    const response = await apiRequest(`/rest/v1/birds_public?${viewQuery}`);
    requireOk(response, 'Anonymous birds_public query');
    const rows = parseJson(response.text, 'Anonymous birds_public query');
    if (!Array.isArray(rows) || rows.length !== 1 || rows[0].id !== publishedBirdId) {
      throw new Error('Expected only the approved, published test bird from birds_public.');
    }
    if ('is_approved' in rows[0] || 'is_published' in rows[0]) {
      throw new Error('The public view exposed publication-control columns.');
    }
    if (Object.keys(rows[0]).some(field => !PUBLIC_BIRD_FIELDS.has(field))) {
      throw new Error('The public view exposed a field outside the approved catalog list.');
    }
    if ([...PUBLIC_BIRD_FIELDS].some(field => !(field in rows[0]))) {
      throw new Error('The public view is missing an expected catalog field.');
    }
  });

  await runCheck('Anonymous direct birds-table access is denied', async () => {
    const response = await apiRequest(
      `/rest/v1/birds?select=*&id=eq.${encodeURIComponent(publishedBirdId)}`
    );
    mustBeDenied(response, 'Anonymous direct birds-table query', ['42501']);
  });

  await runCheck('Staff helper and staff allow-list protections', async () => {
    for (const [role, token, expected] of [
      ['anonymous', undefined, false],
      ['non-staff', nonStaffToken, false],
      ['staff', staffToken, true]
    ]) {
      const response = await apiRequest('/rest/v1/rpc/is_aviary_staff', {
        token,
        method: 'POST',
        body: {}
      });
      requireOk(response, `${role} staff-helper RPC`);
      if (parseJson(response.text, `${role} staff-helper RPC`) !== expected) {
        throw new Error(`${role} staff-helper RPC returned the wrong result.`);
      }
    }

    const readResponse = await apiRequest('/rest/v1/staff_users?select=user_id', {
      token: nonStaffToken
    });
    mustBeDenied(readResponse, 'Non-staff read staff allow-list', ['42501']);

    const insertResponse = await apiRequest('/rest/v1/staff_users', {
      token: nonStaffToken,
      method: 'POST',
      body: { user_id: nonStaffUserId }
    });
    mustBeDenied(insertResponse, 'Non-staff self-promotion insert', ['42501']);
  });

  await runCheck('Anonymous published and unpublished photo authorization', async () => {
    const publishedUrl = await signedPhotoUrl(publishedPhotoPath);
    const imageResponse = await fetchBytesWithTimeout(publishedUrl);
    requireOk(imageResponse, 'Fetch published signed photo');

    const unpublishedResponse = await apiRequest(
      `/storage/v1/object/sign/bird-photos/${unpublishedPhotoPath.split('/').map(encodeURIComponent).join('/')}`,
      { method: 'POST', body: { expiresIn: 300 } }
    );
    await mustBeDenied(unpublishedResponse, 'Anonymous sign unpublished photo');
  });

  await runCheck('Anonymous Storage listing filters unpublished photos', async () => {
    const publishedResponse = await apiRequest('/storage/v1/object/list/bird-photos', {
      method: 'POST',
      body: { prefix: publishedBirdId, limit: 100, offset: 0 }
    });
    requireOk(publishedResponse, 'List published bird photo folder');
    const publishedItems = parseJson(publishedResponse.text, 'List published bird photo folder');
    if (!Array.isArray(publishedItems) ||
        !publishedItems.some(item => item.name === publishedPhotoPath.split('/')[1])) {
      throw new Error('Published photo was not visible in the anonymous folder listing.');
    }

    const unpublishedResponse = await apiRequest('/storage/v1/object/list/bird-photos', {
      method: 'POST',
      body: { prefix: unpublishedBirdId, limit: 100, offset: 0 }
    });
    if (!unpublishedResponse.ok) {
      await mustBeDenied(unpublishedResponse, 'List unpublished bird photo folder');
      return;
    }
    const unpublishedItems = parseJson(
      unpublishedResponse.text,
      'List unpublished bird photo folder'
    );
    if (!Array.isArray(unpublishedItems) || unpublishedItems.length !== 0) {
      throw new Error('Anonymous listing exposed files from an unpublished bird folder.');
    }
  });

  await runCheck('Non-staff sees published rows only', async () => {
    const response = await apiRequest(`/rest/v1/birds?select=id,is_approved,is_published&id=in.${selectedIds}`, {
      token: nonStaffToken
    });
    requireOk(response, 'Non-staff birds query');
    const rows = parseJson(response.text, 'Non-staff birds query');
    if (!Array.isArray(rows) ||
        rows.some(row => row.id !== publishedBirdId || !row.is_approved || !row.is_published)) {
      throw new Error('Non-staff query exposed an unpublished test row.');
    }
  });

  await runCheck('Non-staff cannot sign unpublished photo', async () => {
    const response = await apiRequest(
      `/storage/v1/object/sign/bird-photos/${unpublishedPhotoPath.split('/').map(encodeURIComponent).join('/')}`,
      { token: nonStaffToken, method: 'POST', body: { expiresIn: 300 } }
    );
    await mustBeDenied(response, 'Non-staff sign unpublished photo');
  });

  await runCheck('Anonymous and non-staff cannot write birds or upload photos', async () => {
    const row = {
      common_name: `Unauthorized smoke row ${randomUUID()}`,
      scientific_name: 'Testus nonavis',
      family: 'Testidae',
      category: 'tropical'
    };
    for (const [role, token] of [['anonymous', undefined], ['non-staff', nonStaffToken]]) {
      const insertResponse = await apiRequest('/rest/v1/birds', {
        token,
        method: 'POST',
        headers: { Prefer: 'return=representation' },
        body: row
      });
      if (insertResponse.ok) {
        const insertedRows = parseJson(insertResponse.text, `${role} bird insert`);
        for (const inserted of insertedRows) {
          if (typeof inserted.id === 'string') {
            birdIds.add(inserted.id);
          }
        }
      }
      mustBeDenied(insertResponse, `${role} insert bird`, ['42501']);

      const uploadPath = objectPath(publishedBirdId);
      const uploadResponse = await uploadPhoto(uploadPath, token);
      if (uploadResponse.ok) {
        photoPaths.add(uploadPath);
      }
      await mustBeDenied(uploadResponse, `${role} upload photo`);
    }
  });

  await runCheck('Unauthorized updates and deletes do not change or remove birds', async () => {
    const anonPatch = await apiRequest(
      `/rest/v1/birds?id=eq.${encodeURIComponent(publishedBirdId)}`,
      {
        method: 'PATCH',
        headers: { Prefer: 'return=representation' },
        body: { common_name: `Unauthorized update ${randomUUID()}` }
      }
    );
    mustBeDenied(anonPatch, 'Anonymous update bird', ['42501']);

    const anonDelete = await apiRequest(
      `/rest/v1/birds?id=eq.${encodeURIComponent(unpublishedBirdId)}`,
      {
        method: 'DELETE',
        headers: { Prefer: 'return=representation' }
      }
    );
    mustBeDenied(anonDelete, 'Anonymous delete bird', ['42501']);

    const nonStaffPatch = await apiRequest(
      `/rest/v1/birds?id=eq.${encodeURIComponent(publishedBirdId)}`,
      {
        token: nonStaffToken,
        method: 'PATCH',
        headers: { Prefer: 'return=representation' },
        body: { common_name: `Unauthorized update ${randomUUID()}` }
      }
    );
    mustAffectNoRows(nonStaffPatch, 'Non-staff update bird');

    const nonStaffDelete = await apiRequest(
      `/rest/v1/birds?id=eq.${encodeURIComponent(unpublishedBirdId)}`,
      {
        token: nonStaffToken,
        method: 'DELETE',
        headers: { Prefer: 'return=representation' }
      }
    );
    mustAffectNoRows(nonStaffDelete, 'Non-staff delete bird');

    const staffRead = await apiRequest(
      `/rest/v1/birds?select=id,common_name,is_approved,is_published&id=in.${selectedIds}`,
      { token: staffToken }
    );
    requireOk(staffRead, 'Staff verify unauthorized bird mutations');
    const rows = parseJson(staffRead.text, 'Staff verify unauthorized bird mutations');
    const published = rows.find(row => row.id === publishedBirdId);
    const unpublished = rows.find(row => row.id === unpublishedBirdId);
    if (rows.length !== 2 ||
        published?.common_name !== publishedBirdName ||
        !published.is_approved ||
        !published.is_published ||
        unpublished?.common_name !== unpublishedBirdName ||
        unpublished.is_approved ||
        unpublished.is_published) {
      throw new Error('An unauthorized mutation changed or removed a test bird.');
    }
  });

  await runCheck('Staff publication and photo-path constraints', async () => {
    const publicationResponse = await apiRequest(
      `/rest/v1/birds?id=eq.${encodeURIComponent(unpublishedBirdId)}`,
      {
        token: staffToken,
        method: 'PATCH',
        headers: { Prefer: 'return=minimal' },
        body: { is_published: true }
      }
    );
    mustBeDenied(publicationResponse, 'Publish an unapproved test bird', ['23514']);

    const wrongPathResponse = await setPhotoPath(
      unpublishedBirdId,
      `${publishedBirdId}/wrong-bird.png`,
      staffToken
    );
    mustBeDenied(wrongPathResponse, 'Assign another bird photo folder', ['23514']);

    requireOk(
      await setPhotoPath(unpublishedBirdId, null, staffToken),
      'Clear optional photo_path'
    );
    requireOk(
      await setPhotoPath(unpublishedBirdId, unpublishedPhotoPath, staffToken),
      'Restore unpublished test photo path'
    );
  });

  await runCheck('Staff uploads reject malformed, nonexistent, oversized and GIF objects', async () => {
    for (const malformedPath of [
      'photo.png',
      `not-a-uuid/${randomUUID()}.png`
    ]) {
      const malformedPathResponse = await uploadPhoto(malformedPath, staffToken);
      if (malformedPathResponse.ok) {
        photoPaths.add(malformedPath);
      }
      await mustBeDenied(malformedPathResponse, 'Upload malformed photo path');
    }

    const malformed = await uploadPhoto(`${publishedBirdId}/UPPERCASE.JPG`, staffToken);
    if (malformed.ok) {
      photoPaths.add(`${publishedBirdId}/UPPERCASE.JPG`);
    }
    await mustBeDenied(malformed, 'Upload uppercase-extension photo');

    const nonexistentPath = `${randomUUID()}/${randomUUID()}.png`;
    const nonexistent = await uploadPhoto(nonexistentPath, staffToken);
    if (nonexistent.ok) {
      photoPaths.add(nonexistentPath);
    }
    await mustBeDenied(nonexistent, 'Upload photo for nonexistent bird');

    const gifPath = objectPath(publishedBirdId);
    const gif = await apiRequest(
      `/storage/v1/object/bird-photos/${gifPath.split('/').map(encodeURIComponent).join('/')}`,
      {
        token: staffToken,
        method: 'POST',
        headers: { 'Content-Type': 'image/gif', 'x-upsert': 'false' },
        body: Buffer.from('GIF89a')
      }
    );
    if (gif.ok) {
      photoPaths.add(gifPath);
    }
    await mustBeDenied(gif, 'Upload GIF photo');

    const oversizedPath = objectPath(publishedBirdId);
    const oversized = await apiRequest(
      `/storage/v1/object/bird-photos/${oversizedPath.split('/').map(encodeURIComponent).join('/')}`,
      {
        token: staffToken,
        method: 'POST',
        headers: { 'Content-Type': 'image/png', 'x-upsert': 'false' },
        body: Buffer.alloc(6 * 1024 * 1024),
        timeoutMs: 60000
      }
    );
    if (oversized.ok) {
      photoPaths.add(oversizedPath);
    }
    await mustBeDenied(oversized, 'Upload 6 MB photo');
  });

}

const succeeded = await run();
if (!succeeded) {
  process.exitCode = 1;
}

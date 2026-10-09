const PUBLIC_BIRD_FIELDS = [
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
].join(',');

const PHOTO_PATH_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/[A-Za-z0-9][A-Za-z0-9._-]*\.(jpg|jpeg|png|webp)$/;

const MIN_SIGNED_URL_TTL = 60;
const MAX_SIGNED_URL_TTL = 3600;
const SIGNED_URL_REFRESH_BUFFER = 60;
const REQUEST_TIMEOUT_MS = 10000;

export function formatAvailability(availability, quantityAvailable = null) {
  if (!['available', 'reserved', 'sold'].includes(availability)) {
    throw new TypeError('Availability must be available, reserved, or sold.');
  }

  if (quantityAvailable !== null &&
      (!Number.isInteger(quantityAvailable) || quantityAvailable < 0)) {
    throw new TypeError('Available quantity must be a non-negative integer or null.');
  }

  if ((availability === 'available' && quantityAvailable === 0) ||
      (availability === 'sold' && quantityAvailable > 0)) {
    console.warn('Bird availability and quantity conflict; staff review is needed.');
    return 'Ask us about availability';
  }

  if (availability === 'available' && quantityAvailable !== null) {
    return `Available (${quantityAvailable})`;
  }

  return availability[0].toUpperCase() + availability.slice(1);
}

function readConfig(config) {
  if (!config || typeof config !== 'object') {
    throw new TypeError('Pass a Supabase project URL and publishable key.');
  }

  const { url, publishableKey } = config;
  if (typeof url !== 'string' || typeof publishableKey !== 'string' ||
      !url.trim() || !publishableKey.trim()) {
    throw new TypeError('Supabase URL and publishable key are required.');
  }

  let projectUrl;
  try {
    projectUrl = new URL(url);
  } catch {
    throw new TypeError('Supabase project URL must be a valid absolute URL.');
  }

  const isLocalhost = ['localhost', '127.0.0.1', '[::1]'].includes(projectUrl.hostname);
  if (projectUrl.protocol !== 'https:' && !isLocalhost) {
    throw new TypeError('Supabase project URL must use HTTPS outside localhost.');
  }

  return {
    projectUrl: projectUrl.toString().replace(/\/+$/, ''),
    publishableKey: publishableKey.trim()
  };
}

async function responseData(response, operation) {
  if (!response.ok) {
    throw new Error(`Supabase ${operation} failed (${response.status}).`);
  }

  const body = await response.text();
  if (!body) {
    return null;
  }

  try {
    return JSON.parse(body);
  } catch {
    throw new Error(`Supabase ${operation} returned invalid JSON.`);
  }
}

async function requestJsonWithTimeout(url, options, operation) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    return await responseData(response, operation);
  } catch (error) {
    if (error && error.name === 'AbortError') {
      throw new Error(`Supabase request timed out after ${REQUEST_TIMEOUT_MS} ms.`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function createCatalogDataClient(config) {
  const { projectUrl, publishableKey } = readConfig(config);
  const headers = {
    apikey: publishableKey
  };
  const signedUrlCache = new Map();

  return Object.freeze({
    async listPublishedBirds() {
      const query = new URLSearchParams({
        select: PUBLIC_BIRD_FIELDS,
        order: 'sort_order.asc,common_name.asc'
      });

      const birds = await requestJsonWithTimeout(`${projectUrl}/rest/v1/birds_public?${query}`, {
        method: 'GET',
        headers: {
          ...headers,
          Accept: 'application/json'
        },
        cache: 'no-store'
      }, 'published bird query');

      if (!Array.isArray(birds)) {
        throw new Error('Supabase published bird query did not return a list.');
      }

      return birds;
    },

    async createBirdPhotoUrl(bird, expiresInSeconds = 3600) {
      if (!bird || typeof bird.id !== 'string') {
        throw new TypeError('A bird record with an ID is required for a photo URL.');
      }

      if (typeof bird.photo_path !== 'string' ||
          !PHOTO_PATH_PATTERN.test(bird.photo_path) ||
          bird.photo_path.split('/')[0] !== bird.id) {
        throw new TypeError('Bird photo path is missing or does not match the bird ID.');
      }

      if (!Number.isInteger(expiresInSeconds) ||
          expiresInSeconds < MIN_SIGNED_URL_TTL ||
          expiresInSeconds > MAX_SIGNED_URL_TTL) {
        throw new RangeError(
          `Signed URL expiry must be between ${MIN_SIGNED_URL_TTL} and ${MAX_SIGNED_URL_TTL} seconds.`
        );
      }

      const cacheKey = `${bird.photo_path}:${expiresInSeconds}`;
      const cached = signedUrlCache.get(cacheKey);
      const refreshBuffer = Math.min(
        SIGNED_URL_REFRESH_BUFFER,
        Math.max(10, expiresInSeconds * 0.1)
      );
      if (cached && cached.expiresAt - Date.now() > refreshBuffer * 1000) {
        return cached;
      }

      if (cached && cached.pending) {
        return cached.pending;
      }

      const objectPath = bird.photo_path
        .split('/')
        .map(encodeURIComponent)
        .join('/');
      const endpoint =
        `${projectUrl}/storage/v1/object/sign/bird-photos/${objectPath}`;
      const requestStartedAt = Date.now();
      const pending = (async () => {
        const data = await requestJsonWithTimeout(endpoint, {
          method: 'POST',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
            Accept: 'application/json'
          },
          body: JSON.stringify({ expiresIn: expiresInSeconds }),
          cache: 'no-store'
        }, 'signed photo URL request');

        if (!data || typeof data.signedURL !== 'string' || !data.signedURL) {
          throw new Error('Supabase signed photo URL response did not include signedURL.');
        }

        let signedUrl;
        if (/^https?:\/\//i.test(data.signedURL)) {
          signedUrl = new URL(data.signedURL);
        } else if (data.signedURL.startsWith('/storage/v1/')) {
          signedUrl = new URL(data.signedURL, projectUrl);
        } else if (data.signedURL.startsWith('/object/')) {
          signedUrl = new URL(`/storage/v1${data.signedURL}`, projectUrl);
        } else {
          const storageBaseUrl = new URL('/storage/v1/', projectUrl);
          signedUrl = new URL(data.signedURL.replace(/^\/+/, ''), storageBaseUrl);
        }
        if (signedUrl.origin !== new URL(projectUrl).origin) {
          throw new Error('Supabase signed photo URL returned an unexpected origin.');
        }

        const signedPhoto = Object.freeze({
          url: signedUrl.toString(),
          expiresAt: requestStartedAt + expiresInSeconds * 1000
        });
        signedUrlCache.set(cacheKey, signedPhoto);
        return signedPhoto;
      })();

      signedUrlCache.set(cacheKey, { pending });
      try {
        return await pending;
      } catch (error) {
        signedUrlCache.delete(cacheKey);
        throw error;
      }
    }
  });
}

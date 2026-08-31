// Helpers de cliente compartidos por todas las paginas.
// El "modo seguro" se activa con ?safe=1 en la URL de la pagina y se propaga
// tanto a las llamadas al backend como al modo de renderizado del front.

export const SAFE = new URLSearchParams(location.search).get('safe') === '1';
export const SP = SAFE ? '?safe=1' : '';

// Anade safe=1 a una ruta si el modo seguro esta activo.
export function withSafe(url) {
  if (!SAFE) return url;
  return url + (url.includes('?') ? '&' : '?') + 'safe=1';
}

// Conserva el modo al navegar entre paginas.
export function link(path) {
  return path + SP;
}

// Llamada a la API (mismo origen -> cookies incluidas).
export async function api(path, opts = {}) {
  const res = await fetch(withSafe('/api' + path), {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...opts,
  });
  let data = null;
  try { data = await res.json(); } catch (_) {}
  return { status: res.status, data };
}

export async function getMe() {
  const { data } = await api('/me');
  return data; // { user, csrf }
}

// Redirige a login si no hay sesion; devuelve el usuario si la hay.
export async function requireLogin() {
  const { user } = await getMe();
  if (!user) { location.href = link('/'); return null; }
  return user;
}

export function esc(s) {
  const d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
}

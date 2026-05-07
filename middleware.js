// Vercel Edge Middleware — form-based login gate.
//
// Replaces HTTP Basic Auth (which Chrome has been deprecating) with a proper
// login form. Same env-var-driven credentials; better browser compatibility.
//
// Flow:
//   1. Any request lacking a valid `oracle_session` cookie → render the login form.
//   2. POST /__login validates the submitted user+pass against env vars; on
//      success, sets an HMAC-signed session cookie (30-day expiry) and 302's
//      back to "/".
//   3. Subsequent requests with a valid cookie pass through to the static site.
//
// Required env vars (Production environment in Vercel):
//   AUTH_USER  — e.g. "neyland"
//   AUTH_PASS  — long random string, used as both password and HMAC secret

export const config = {
  matcher: [
    // Skip static assets that don't need protection / can't run middleware
    '/((?!favicon\\.ico|robots\\.txt|_vercel/.*).*)',
  ],
};

const COOKIE_NAME = 'oracle_session';
const COOKIE_TTL_SEC = 30 * 24 * 60 * 60; // 30 days

// HMAC-SHA256 sign with Web Crypto API (Edge runtime supports this)
async function hmacHex(message, secret) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(message));
  return Array.from(new Uint8Array(sig))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

function loginFormHTML(errorMsg) {
  const errBlock = errorMsg
    ? `<div class="err">${errorMsg}</div>`
    : '';
  return `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in — Oracle</title>
<style>
:root { color-scheme: light; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: linear-gradient(135deg, #1F3864 0%, #0F1F3D 100%);
  display: grid;
  place-items: center;
  color: #1a1a1a;
}
.card {
  background: white;
  padding: 40px 36px;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.25);
  width: 360px;
  max-width: calc(100vw - 32px);
}
.brand {
  text-align: center;
  margin-bottom: 28px;
  padding-bottom: 18px;
  border-bottom: 3px solid #BF9000;
}
.brand h1 {
  color: #1F3864;
  font-size: 24px;
  letter-spacing: 1.5px;
  margin: 0 0 6px;
  font-weight: 800;
}
.brand .sub {
  color: #5a5a60;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #5a5a60;
  margin-bottom: 6px;
  font-weight: 700;
}
input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #d8d8dc;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 18px;
  font-family: inherit;
}
input:focus {
  outline: none;
  border-color: #1F3864;
  box-shadow: 0 0 0 3px rgba(31, 56, 100, 0.12);
}
button {
  width: 100%;
  background: #1F3864;
  color: white;
  border: 0;
  padding: 13px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.4px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s ease;
}
button:hover { background: #2A4A7C; }
button:active { transform: translateY(1px); }
.err {
  background: #fde8e8;
  color: #a51616;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 16px;
  border-left: 3px solid #a51616;
}
.foot {
  text-align: center;
  margin-top: 18px;
  font-size: 11px;
  color: #8b8b91;
}
</style>
</head><body>
<form class="card" method="POST" action="/__login">
  <div class="brand">
    <h1>ORACLE</h1>
    <div class="sub">Neyland Development</div>
  </div>
  ${errBlock}
  <label for="u">Username</label>
  <input id="u" type="text" name="username" autocomplete="username" autofocus required>
  <label for="p">Password</label>
  <input id="p" type="password" name="password" autocomplete="current-password" required>
  <button type="submit">Sign In</button>
  <div class="foot">Confidential · internal use only</div>
</form>
</body></html>`;
}

function htmlResponse(html, status = 200) {
  return new Response(html, {
    status,
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

export default async function middleware(request) {
  const url = new URL(request.url);
  const user = process.env.AUTH_USER;
  const pass = process.env.AUTH_PASS;

  if (!user || !pass) {
    return new Response(
      'Server is missing AUTH_USER / AUTH_PASS env vars. Set them in Vercel → Settings → Environment Variables (Production).',
      { status: 500, headers: { 'content-type': 'text/plain' } }
    );
  }

  // === Login POST handler ===
  if (url.pathname === '/__login' && request.method === 'POST') {
    const form = await request.formData();
    const submittedUser = (form.get('username') || '').toString();
    const submittedPass = (form.get('password') || '').toString();

    if (submittedUser === user && submittedPass === pass) {
      const expiresMs = Date.now() + COOKIE_TTL_SEC * 1000;
      const payload = String(expiresMs);
      const sig = await hmacHex(payload, pass);
      const token = `${payload}.${sig}`;
      return new Response(null, {
        status: 302,
        headers: {
          location: '/',
          'set-cookie':
            `${COOKIE_NAME}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${COOKIE_TTL_SEC}`,
        },
      });
    }

    return htmlResponse(loginFormHTML('Wrong username or password.'), 401);
  }

  // === Login form GET ===
  if (url.pathname === '/__login') {
    return htmlResponse(loginFormHTML());
  }

  // === Cookie check for every other path ===
  const cookieHeader = request.headers.get('cookie') || '';
  const match = cookieHeader.match(new RegExp(`(?:^|;\\s*)${COOKIE_NAME}=([^;]+)`));

  if (match) {
    const [payloadStr, sig] = match[1].split('.');
    if (payloadStr && sig) {
      const expectedSig = await hmacHex(payloadStr, pass);
      const exp = parseInt(payloadStr, 10);
      if (sig === expectedSig && Number.isFinite(exp) && exp > Date.now()) {
        return; // valid session — pass through to static asset
      }
    }
  }

  // No / bad / expired cookie → render login form (200 so browser shows it)
  return htmlResponse(loginFormHTML());
}

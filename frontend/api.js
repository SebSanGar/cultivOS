// Shared API client for cultivOS frontend.
// Centralizes Authorization header, 401 redirect, and JSON parsing.
// Import in HTML BEFORE page-specific scripts:
//   <script src="/api.js"></script>

(function (global) {
  "use strict";

  const TOKEN_KEY = "cultivos_token";
  const LOGIN_PATH = "/login";

  function getToken() {
    try { return localStorage.getItem(TOKEN_KEY) || ""; }
    catch (_) { return ""; }
  }

  function setToken(token) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch (_) { /* storage disabled */ }
  }

  function buildHeaders(extra) {
    const h = Object.assign({ "Accept": "application/json" }, extra || {});
    const t = getToken();
    if (t) h["Authorization"] = "Bearer " + t;
    return h;
  }

  async function request(path, opts) {
    opts = opts || {};
    const init = {
      method: opts.method || "GET",
      headers: buildHeaders(opts.headers),
      credentials: opts.credentials || "same-origin",
    };
    if (opts.body !== undefined) {
      if (typeof opts.body === "object" && !(opts.body instanceof FormData)) {
        init.headers["Content-Type"] = init.headers["Content-Type"] || "application/json";
        init.body = JSON.stringify(opts.body);
      } else {
        init.body = opts.body;
      }
    }

    let resp;
    try {
      resp = await fetch(path, init);
    } catch (err) {
      throw new ApiError("network", 0, String(err && err.message || err));
    }

    if (resp.status === 401) {
      setToken("");
      if (opts.redirectOn401 !== false && location.pathname !== LOGIN_PATH) {
        const next = encodeURIComponent(location.pathname + location.search);
        location.href = LOGIN_PATH + "?next=" + next;
      }
      throw new ApiError("unauthorized", 401, "Not authenticated");
    }

    let data = null;
    const ct = resp.headers.get("content-type") || "";
    if (ct.indexOf("application/json") !== -1) {
      try { data = await resp.json(); } catch (_) { data = null; }
    } else if (opts.parse !== "none") {
      try { data = await resp.text(); } catch (_) { data = null; }
    }

    if (!resp.ok) {
      const msg = (data && data.detail) || (data && data.message) || resp.statusText || "HTTP " + resp.status;
      throw new ApiError("http", resp.status, msg, data);
    }
    return data;
  }

  function ApiError(kind, status, message, body) {
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.message = message;
    this.body = body || null;
  }
  ApiError.prototype = Object.create(Error.prototype);
  ApiError.prototype.constructor = ApiError;

  const api = {
    get:    (path, opts)       => request(path, Object.assign({ method: "GET" }, opts || {})),
    post:   (path, body, opts) => request(path, Object.assign({ method: "POST", body }, opts || {})),
    put:    (path, body, opts) => request(path, Object.assign({ method: "PUT",  body }, opts || {})),
    del:    (path, opts)       => request(path, Object.assign({ method: "DELETE" }, opts || {})),
    patch:  (path, body, opts) => request(path, Object.assign({ method: "PATCH", body }, opts || {})),
    getToken,
    setToken,
    ApiError,
  };

  global.cultivosApi = api;
  global.api = global.api || api;
})(typeof window !== "undefined" ? window : globalThis);

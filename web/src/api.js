const API_BASE = import.meta.env.VITE_API_URL || "";

const API_BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
  } catch {
    throw new Error(
      "Cannot reach the game server. Start the API first: " +
        "wsl bash scripts/run_web.sh (or python run_server.py in WSL/Linux).",
    );
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    if (response.status === 502 || response.status === 503) {
      throw new Error(
        typeof detail === "string"
          ? detail
          : "Game server unavailable. Build the C backend with: make dist",
      );
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  return response.json();
}

export function createGame(playerName) {
  return request("/api/games", {
    method: "POST",
    body: JSON.stringify({ player_name: playerName }),
  });
}

export function move(sessionId, direction) {
  return request(`/api/games/${sessionId}/move`, {
    method: "POST",
    body: JSON.stringify({ direction }),
  });
}

export function portal(sessionId) {
  return request(`/api/games/${sessionId}/portal`, { method: "POST" });
}

export function resetGame(sessionId) {
  return request(`/api/games/${sessionId}/reset`, { method: "POST" });
}

export function healthCheck() {
  return request("/api/health");
}

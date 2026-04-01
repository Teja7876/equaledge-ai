export interface Env {
  BACKEND_URL: string
  API_SECRET: string
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)

    // --- Health check ---
    if (url.pathname === "/health") {
      return json({ status: "ok", service: "EqualEdge Gateway" }, 200)
    }

    // --- CORS preflight ---
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders()
      })
    }

    // --- Route API traffic ---
    if (url.pathname.startsWith("/api")) {
      try {
        const backendURL = env.BACKEND_URL + url.pathname

        const response = await fetch(backendURL, {
          method: request.method,
          headers: {
            ...Object.fromEntries(request.headers),
            "x-edge-auth": env.API_SECRET
          },
          body: request.body
        })

        return new Response(response.body, {
          status: response.status,
          headers: {
            ...Object.fromEntries(response.headers),
            ...corsHeaders()
          }
        })

      } catch (error) {
        return json({ error: "Backend unavailable" }, 502)
      }
    }

    // --- Default fallback ---
    return json({ message: "EqualEdge Gateway Active" }, 200)
  }
} satisfies ExportedHandler<Env>

// --- Helpers ---

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders()
    }
  })
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  }
}
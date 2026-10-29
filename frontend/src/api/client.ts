const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function buildUrl(path: string): string {
  if (!API_BASE_URL) {
    throw new Error("VITE_API_BASE_URL is not defined");
  }

  const base = API_BASE_URL.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildUrl(path);
  const headers = new Headers(options.headers || {});

  if (options.body !== undefined && options.body !== null && !(options.body instanceof FormData)) {
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw error;
    }
    throw new Error(
      `Network error while fetching ${url}: ${error instanceof Error ? error.message : String(error)}`
    );
  }

  const contentType = response.headers.get("content-type") || "";
  let data: unknown;

  if (contentType.includes("application/json")) {
    try {
      data = await response.json();
    } catch {
      throw new Error(`Failed to parse JSON response from ${url}`);
    }
  } else {
    try {
      const text = await response.text();
      if (text.trim()) {
        data = text;
      }
    } catch {
      data = undefined;
    }
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status} ${response.statusText}`;

    if (typeof data === "string" && data.trim()) {
      message = data.trim();
    } else if (data && typeof data === "object") {
      const maybeDetail = (data as Record<string, unknown>).detail;
      if (typeof maybeDetail === "string" && maybeDetail.trim()) {
        message = maybeDetail;
      } else {
        try {
          message = JSON.stringify(data);
        } catch {
          // keep default message
        }
      }
    }

    throw new Error(message);
  }

  return data as T;
}

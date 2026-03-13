export const apiClient = {
  chatStream: "/api/chat/stream",
  chatAttachments: "/api/chat/attachments",
  upload: "/api/upload",
  documents: "/api/documents",
  memory: "/api/memory",
  retrievalDebug: "/api/retrieval/debug",
  sessions: "/api/sessions",
};

type JSONValue = string | number | boolean | null | JSONValue[] | { [key: string]: JSONValue };

export interface APIErrorPayload {
  error: string;
  code: string;
  details?: Record<string, JSONValue>;
}

export class APIClientError extends Error {
  status: number;
  code: string;
  details: Record<string, JSONValue>;

  constructor(status: number, payload: APIErrorPayload) {
    super(payload.error);
    this.name = "APIClientError";
    this.status = status;
    this.code = payload.code;
    this.details = payload.details ?? {};
  }
}

async function readErrorPayload(response: Response): Promise<APIErrorPayload> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const payload = (await response.json()) as Partial<APIErrorPayload>;
    return {
      error: payload.error ?? `请求失败，状态码 ${response.status}`,
      code: payload.code ?? "request_error",
      details: payload.details ?? {},
    };
  }
  return {
    error: (await response.text()) || `请求失败，状态码 ${response.status}`,
    code: "request_error",
    details: {},
  };
}

async function ensureOk(response: Response): Promise<Response> {
  if (!response.ok) {
    throw new APIClientError(response.status, await readErrorPayload(response));
  }
  return response;
}

export async function getJSON<T>(url: string): Promise<T> {
  const response = await ensureOk(await fetch(url));
  return (await response.json()) as T;
}

export async function sendJSON<T>(url: string, method: string, payload?: unknown): Promise<T> {
  const response = await ensureOk(
    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: payload === undefined ? undefined : JSON.stringify(payload),
    }),
  );
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function sendForm<T>(url: string, method: string, payload: FormData): Promise<T> {
  const response = await ensureOk(
    await fetch(url, {
      method,
      body: payload,
    }),
  );
  return (await response.json()) as T;
}

export interface SSEHandlers {
  onEvent?: (event: string, data: Record<string, unknown>) => void;
  onToolCall?: (data: Record<string, unknown>) => void;
  onToken?: (data: Record<string, unknown>) => void;
  onRetrievalDebug?: (data: Record<string, unknown>) => void;
  onFinalAnswer?: (data: Record<string, unknown>) => void;
  onError?: (data: Record<string, unknown>) => void;
}

function parseEventChunk(chunk: string): { event: string; data: Record<string, unknown> } | null {
  const lines = chunk
    .split("\n")
    .map((line) => line.trimEnd())
    .filter(Boolean);
  if (!lines.length) {
    return null;
  }

  let event = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  const rawData = dataLines.join("\n");
  if (!rawData) {
    return null;
  }

  return {
    event,
    data: JSON.parse(rawData) as Record<string, unknown>,
  };
}

export async function postEventStream(url: string, payload: unknown, handlers: SSEHandlers): Promise<void> {
  const response = await ensureOk(
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("当前浏览器不支持流式响应。");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (eventName: string, data: Record<string, unknown>) => {
    handlers.onEvent?.(eventName, data);
    switch (eventName) {
      case "tool_call":
        handlers.onToolCall?.(data);
        break;
      case "token":
        handlers.onToken?.(data);
        break;
      case "retrieval_debug":
        handlers.onRetrievalDebug?.(data);
        break;
      case "final_answer":
        handlers.onFinalAnswer?.(data);
        break;
      case "error":
        handlers.onError?.(data);
        break;
      default:
        break;
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");

    let boundaryIndex = buffer.indexOf("\n\n");
    while (boundaryIndex !== -1) {
      const chunk = buffer.slice(0, boundaryIndex);
      buffer = buffer.slice(boundaryIndex + 2);
      const parsed = parseEventChunk(chunk);
      if (parsed) {
        dispatch(parsed.event, parsed.data);
      }
      boundaryIndex = buffer.indexOf("\n\n");
    }

    if (done) {
      break;
    }
  }

  const parsed = parseEventChunk(buffer);
  if (parsed) {
    dispatch(parsed.event, parsed.data);
  }
}

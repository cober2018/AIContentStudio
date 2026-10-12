// API 客户端：V1 开发模式身份走 X-Studio-User header，可在设置页切换
const USER_KEY = "studio-user";

export function currentUser(): string {
  return localStorage.getItem(USER_KEY) || "admin@studio.local";
}

export function setCurrentUser(email: string): void {
  localStorage.setItem(USER_KEY, email);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(method: string, path: string, body?: unknown, options: { isForm?: boolean; signal?: AbortSignal } = {}): Promise<T> {
  const headers: Record<string, string> = { "X-Studio-User": currentUser() };
  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (options.isForm) {
      payload = body as FormData;
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }
  const resp = await fetch(`/api/v1${path}`, { method, headers, body: payload, signal: options.signal });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}));
    const value = detail.detail;
    throw new ApiError(resp.status, typeof value === "string" ? value : typeof value?.code === "string" ? value.code : `HTTP ${resp.status}`, value);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>("GET", path, undefined, { signal }),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
  upload: <T>(path: string, form: FormData) => request<T>("POST", path, form, { isForm: true }),
};

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

export type ChannelFormField = {
  path: string; type: string; label?: string; required?: boolean; readonly?: boolean; default?: unknown;
  min_length?: number; max_length?: number; minimum?: number; maximum?: number; pattern?: string;
  enum?: unknown[]; min_items?: number; max_items?: number; ordered?: boolean; unique_ids?: boolean;
  unique_values?: boolean; global_unique_ids?: boolean; additional_fields?: boolean; exact_evidence_ref?: boolean;
  fields?: ChannelFormField[]; item?: ChannelFormField; discriminator?: string;
  variants?: Record<string, Record<string, ChannelFormField>>; first_kind?: string;
  kind_counts?: Record<string, { min?: number; max?: number }>;
};
export type ChannelFormDescriptor = {
  descriptor_version: number; channel_id?: string; content_form?: string; schema_id: string; schema_version?: string;
  fields: ChannelFormField[]; additional_fields?: boolean;
  media_roles?: { role: string; required?: boolean; exact_slot?: boolean; max_items?: number }[];
  error_mapping?: Record<string, { path: string; message: string }>;
  technical_limits?: { canonical_bytes?: number; platform_verified?: boolean };
};

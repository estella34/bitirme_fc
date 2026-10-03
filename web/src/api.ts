import type {
  DecodeResult,
  DemoStatus,
  LocationDetail,
  LocationState,
  ReviewItem,
  Scan,
  Summary,
  Twin,
  Warehouse,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* gövde JSON değil */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  warehouses: () => request<Warehouse[]>("/api/warehouses"),
  twin: (id: number) => request<Twin>(`/api/warehouses/${id}/twin`),
  map: (id: number) => request<{ resolution: number; cells: number[] }>(`/api/warehouses/${id}/map`),
  summary: (id: number) => request<Summary>(`/api/warehouses/${id}/summary`),
  location: (id: number) => request<LocationDetail>(`/api/locations/${id}`),
  review: (warehouseId: number) => request<ReviewItem[]>(`/api/review?warehouse_id=${warehouseId}`),
  reviewAction: (observationId: number, action: "approve" | "correct", note?: string) =>
    request<LocationState>(`/api/observations/${observationId}/review`, json({ action, note })),
  scans: (warehouseId: number) => request<Scan[]>(`/api/scans?warehouse_id=${warehouseId}`),
  demo: () => request<DemoStatus>("/api/demo"),
  demoStart: (speed: number) => request<DemoStatus>("/api/demo/start", json({ speed })),
  demoStop: () => request<DemoStatus>("/api/demo/stop", { method: "POST" }),
  decode: (file: File) => {
    const fd = new FormData();
    fd.append("image", file);
    return request<DecodeResult>("/api/decode", { method: "POST", body: fd });
  },
  exportUrl: (scanId: string) => `/api/scans/${encodeURIComponent(scanId)}/export.csv`,
};

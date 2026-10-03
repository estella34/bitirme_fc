export type Status = "verified" | "observed" | "unreadable" | "empty" | "conflict";
export type ReviewStatus = "none" | "pending" | "approved" | "corrected";

export interface Warehouse {
  id: number;
  code: string;
  name: string;
  width_m: number;
  length_m: number;
}

export interface LocationState {
  id: number;
  code: string;
  rack_id: number;
  level: number;
  position: number;
  expected: string[];
  status: Status | null;
  reason: string | null;
  codes: string[];
  missing: string[];
  unexpected: string[];
  box_count: number | null;
  review_status: ReviewStatus | null;
  observation_id: number | null;
  scan_id: string | null;
  updated_at: string | null;
}

export interface Rack {
  id: number;
  code: string;
  aisle: string | null;
  levels: number;
  positions: number;
  x: number;
  y: number;
  yaw_deg: number;
  bay_width_m: number;
  depth_m: number;
  level_height_m: number;
  locations: LocationState[];
}

export interface RobotState {
  x: number;
  y: number;
  yaw: number;
  mast_mm: number;
  state: string;
  online: boolean;
}

export interface Twin {
  warehouse: Warehouse;
  racks: Rack[];
  robot: RobotState;
  trail: [number, number][];
}

export interface CodeRead {
  text: string;
  symbology: string;
  method: string;
  confidence?: number;
  polygon: number[][];
}

export interface Capture {
  id: number;
  scan_id: string;
  location_id: number | null;
  location_code: string | null;
  camera_id: string;
  vertical_position_mm: number | null;
  image_url: string;
  thumb_url: string;
  width: number;
  height: number;
  sharpness: number;
  decode_ms: number;
  captured_at: string;
  reads: CodeRead[];
}

export interface LocationDetail extends LocationState {
  rack_code: string;
  camera_height_mm: number | null;
  expected_items: { code: string; description: string | null; quantity: number }[];
  review_note: string | null;
  captures: Capture[];
  history: { scan_id: string; status: Status; updated_at: string }[];
}

export interface Scan {
  id: string;
  warehouse_id: number;
  status: "running" | "completed" | "failed" | "cancelled";
  mode: "robot" | "manual" | "demo";
  note: string | null;
  started_at: string;
  finished_at: string | null;
  counts: Partial<Record<Status, number>>;
}

export interface Summary {
  locations: number;
  scanned: number;
  by_status: Partial<Record<Status, number>>;
  pending_review: number;
  verified_ratio: number | null;
  last_scan: Scan | null;
}

export interface DemoStatus {
  running: boolean;
  warehouse_id?: number;
  speed?: number;
  progress?: number;
  scenario?: string[];
  scan_id?: string;
  result?: {
    anomalies: number;
    detected: number;
    false_alarms: number;
    details: Record<string, string>;
  } | null;
}

export interface FeedEvent {
  id: number;
  ts: string;
  level: "info" | "ok" | "warn" | "error";
  text: string;
  location_id?: number;
}

export interface ReviewItem extends LocationState {
  thumb_url: string | null;
}

export interface DecodeResult {
  width: number;
  height: number;
  sharpness: number;
  elapsed_ms: number;
  methods_tried: string[];
  codes: CodeRead[];
}

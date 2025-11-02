export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
}

export type { ScanStartRequest, ScanStatusResponse } from "@/api/scan";

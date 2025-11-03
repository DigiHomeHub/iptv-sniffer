import apiClient from "./client";
import type { Channel } from "@/types/channel";

export type ScanMode = "template" | "multicast" | "m3u_batch";

export interface ScanStartRequest {
  mode: ScanMode;
  base_url?: string;
  start_ip?: string;
  end_ip?: string;
  protocol?: string;
  ip_ranges?: string[];
  ports?: number[];
  timeout?: number;
  preset?: string;
}

export interface ScanStartResponse {
  scan_id: string;
  status: "pending" | "running" | "completed" | "cancelled" | "failed";
  total: number;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: "pending" | "running" | "completed" | "cancelled" | "failed";
  progress: number;
  total: number;
  valid: number;
  invalid: number;
  started_at: string;
  completed_at?: string;
  error?: string;
  channels?: Channel[];
}

export const scanAPI = {
  async start(payload: ScanStartRequest): Promise<ScanStartResponse> {
    const response = await apiClient.post<ScanStartResponse>("/scan/start", payload);
    return response.data;
  },

  async getStatus(scanId: string): Promise<ScanStatusResponse> {
    const response = await apiClient.get<ScanStatusResponse>(`/scan/${scanId}`);
    return response.data;
  },

  async cancel(scanId: string): Promise<{ scan_id: string; status: string; cancelled: boolean }> {
    const response = await apiClient.delete<{ scan_id: string; status: string; cancelled: boolean }>(
      `/scan/${scanId}`,
    );
    return response.data;
  },
};

export default { scanAPI };

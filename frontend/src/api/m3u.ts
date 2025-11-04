import { config } from "@/config";

export interface M3UImportResult {
  imported: number;
  failed: number;
  channels: unknown[];
  errors: string[];
}

const BASE_URL = config.apiBaseURL.replace(/\/$/, "");

export async function importM3U(file: File): Promise<M3UImportResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/m3u/import`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail?.detail ?? "Failed to import playlist");
  }

  return await response.json();
}

export function exportM3U(params: {
  group?: string;
  resolution?: string;
  status?: string;
} = {}): void {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      searchParams.append(key, value);
    }
  });

  const url = `${BASE_URL}/m3u/export${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
  window.location.href = url;
}

export default {
  import: importM3U,
  export: exportM3U,
};

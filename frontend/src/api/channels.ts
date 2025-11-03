import apiClient from "@/api/client";
import type { Channel } from "@/types/channel";

export interface ChannelListParams {
  page?: number;
  page_size?: number;
  group?: string;
  resolution?: string;
  status?: string;
  search?: string;
}

export interface ChannelListResponse {
  channels: Channel[];
  total: number;
  page: number;
  pages: number;
}

export const channelsAPI = {
  async list(params: ChannelListParams = {}): Promise<ChannelListResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.append(key, String(value));
      }
    });
    const response = await apiClient.get<ChannelListResponse>(`/channels?${searchParams.toString()}`);
    return response.data;
  },

  async get(channelId: string): Promise<Channel> {
    const response = await apiClient.get<Channel>(`/channels/${channelId}`);
    return response.data;
  },

  async update(channelId: string, payload: Partial<Channel>): Promise<Channel> {
    const response = await apiClient.put<Channel>(`/channels/${channelId}`, payload);
    return response.data;
  },

  async delete(channelId: string): Promise<void> {
    await apiClient.delete(`/channels/${channelId}`);
  },
};

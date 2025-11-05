import apiClient from "@/api/client";
import type { Channel } from "@/types/channel";

export interface GroupStatistics {
  name: string;
  total: number;
  online: number;
  offline: number;
  online_percentage: number;
}

export interface GroupListResponse {
  groups: GroupStatistics[];
  total_groups: number;
}

export interface GroupChannelsResponse {
  channels: Channel[];
  total: number;
  page: number;
  pages: number;
}

export const groupsAPI = {
  async list(): Promise<GroupListResponse> {
    const response = await apiClient.get<GroupListResponse>("/groups");
    return response.data;
  },

  async getChannels(groupName: string, page = 1, pageSize = 50): Promise<GroupChannelsResponse> {
    const response = await apiClient.get<GroupChannelsResponse>(
      `/groups/${encodeURIComponent(groupName)}/channels`,
      {
        params: {
          page,
          page_size: pageSize,
        },
      },
    );
    return response.data;
  },

  async merge(sourceGroups: string[], targetGroup: string): Promise<{ merged: number; target_group: string }> {
    const response = await apiClient.post<{ merged: number; target_group: string }>("/groups/merge", {
      source_groups: sourceGroups,
      target_group: targetGroup,
    });
    return response.data;
  },

  async rename(groupName: string, newName: string): Promise<{ renamed: number; new_name: string }> {
    const response = await apiClient.put<{ renamed: number; new_name: string }>(
      `/groups/${encodeURIComponent(groupName)}`,
      { new_name: newName },
    );
    return response.data;
  },

  async delete(groupName: string): Promise<{ deleted: boolean; affected_channels: number }> {
    const response = await apiClient.delete<{ deleted: boolean; affected_channels: number }>(
      `/groups/${encodeURIComponent(groupName)}`,
    );
    return response.data;
  },
};

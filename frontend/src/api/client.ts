import axios from "axios";

import { config } from "@/config";

const apiClient = axios.create({
  baseURL: config.apiBaseURL,
  timeout: config.apiTimeout,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      (error.response?.data as { detail?: string })?.detail ??
      error.message ??
      "Request failed";
    // eslint-disable-next-line no-console
    console.error("API request failed:", message, error.response);
    return Promise.reject(new Error(message));
  },
);

export default apiClient;

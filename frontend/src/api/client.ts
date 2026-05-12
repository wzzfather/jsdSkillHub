import axios from "axios";
import { ElMessage } from "element-plus";
import { translate } from "@/locales";

export const api = axios.create({
  baseURL: "/api",
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      if (window.location.pathname !== "/login") {
        ElMessage.warning(translate("auth.sessionExpired"));
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);

import { api } from "./client";
import type { UserPublic, UserMeResponse, SendCodeResponse } from "./types";

export interface CaptchaImageResponse {
  captcha_id: string;
  image: string;
}

export async function login(payload: { username?: string; email?: string; password: string }) {
  return api.post<{ access_token: string; token_type: string }>("/auth/login", payload);
}

/** GET /api/captcha/image — image 为 PNG 的裸 base64（前端需加 data URL 前缀） */
export async function getCaptchaImage() {
  return api.get<CaptchaImageResponse>("/captcha/image");
}

export async function register(payload: {
  username: string;
  password: string;
  email?: string | null;
  captcha_id: string;
  captcha_code: string;
}) {
  return api.post<UserPublic>("/auth/register", payload);
}

/** MVP：请求后端生成验证码；生产环境接入 SMTP 后仅发邮件、响应体不再含 code */
export async function sendCode(email: string) {
  return api.post<SendCodeResponse>("/auth/send-code", { email });
}

export async function verifyEmail(email: string, code: string) {
  return api.post<{ access_token: string; token_type: string }>("/auth/verify-email", { email, code });
}

/** GET /api/auth/me — 当前登录用户资料 */
export async function fetchCurrentUser() {
  return api.get<UserMeResponse>("/auth/me");
}

/** PUT /api/auth/me — 更新用户名 / 邮箱（至少一项；服务端校验唯一性与格式） */
export async function updateProfile(data: { username?: string; email?: string | null }) {
  return api.put<UserMeResponse>("/auth/me", data);
}

/** PUT /api/auth/change-password — 修改密码，响应含新 access_token */
export async function changePassword(data: { current_password: string; new_password: string }) {
  return api.put<{ access_token: string; token_type: string }>("/auth/change-password", data);
}

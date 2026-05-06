import { api } from "./client";
import type { UserPublic } from "./types";

export async function login(payload: { username: string; password: string }) {
  return api.post<{ access_token: string; token_type: string }>("/auth/login", payload);
}

export async function register(payload: { username: string; password: string }) {
  return api.post<UserPublic>("/auth/register", payload);
}

import { api } from "./client";
import type {
  ActionResponse,
  DownloadResponse,
  InstallResponse,
  Paginated,
  Skill,
  SkillAdmin,
  SkillDetail,
} from "./types";

export async function fetchSkills(params?: {
  status?: string;
  page?: number;
  page_size?: number;
  category?: string;
  sort?: string;
  search?: string;
}) {
  return api.get<Paginated<Skill>>("/skills", { params });
}

export async function fetchAdminSkills(params?: { status?: string; page?: number; page_size?: number }) {
  return api.get<Paginated<SkillAdmin>>("/skills/admin/all", { params });
}

export async function fetchMySkills(params?: { page?: number; page_size?: number }) {
  return api.get<Paginated<Skill>>("/skills/mine", { params });
}

export async function fetchSkillDetail(id: string) {
  return api.get<SkillDetail>(`/skills/${id}`);
}

export async function uploadSkill(form: FormData) {
  return api.post<Skill>("/skills/upload", form);
}

export async function downloadSkill(id: string) {
  return api.get<DownloadResponse>(`/skills/${id}/download`);
}

export async function installSkill(id: string) {
  return api.post<InstallResponse>(`/skills/${id}/install`);
}

export async function offlineSkill(id: string, comment: string) {
  return api.post<ActionResponse>(`/skills/${id}/offline`, { comment });
}

export async function resubmitSkill(id: string) {
  return api.post<ActionResponse>(`/skills/${id}/resubmit`, {});
}

export async function republishSkill(id: string) {
  return api.post<ActionResponse>(`/skills/${id}/republish`, {});
}

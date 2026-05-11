import { api } from "./client";
import type {
  ActionResponse,
  DownloadResponse,
  Paginated,
  Skill,
  SkillAdmin,
  SkillDetail,
  SkillVersion,
} from "./types";

export async function fetchSkills(params?: {
  status?: string;
  page?: number;
  page_size?: number;
  category?: string;
  sort?: string;
  search?: string;
  author?: string;
}) {
  return api.get<Paginated<Skill>>("/skills", { params });
}

export async function fetchSkillCategories() {
  return api.get<{ items: string[] }>("/skills/categories");
}

export async function fetchAdminSkills(params?: {
  status?: string;
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  author?: string;
}) {
  return api.get<Paginated<SkillAdmin>>("/skills/admin/all", { params });
}

export async function fetchMySkills(params?: { page?: number; page_size?: number }) {
  return api.get<Paginated<Skill>>("/skills/mine", { params });
}

export async function fetchSkillDetail(id: string) {
  return api.get<SkillDetail>(`/skills/${id}`);
}

export async function fetchSkillVersions(skillId: string): Promise<SkillVersion[]> {
  const { data } = await api.get<SkillVersion[]>(`/skills/${skillId}/versions`);
  return data;
}

export async function deprecateSkill(skillId: string, message: string): Promise<ActionResponse> {
  const { data } = await api.post<ActionResponse>(`/skills/${skillId}/deprecate`, { message });
  return data;
}

export async function uploadSkill(form: FormData) {
  return api.post<Skill>("/skills/upload", form);
}

export async function downloadSkill(id: string) {
  return api.get<DownloadResponse>(`/skills/${id}/download`);
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

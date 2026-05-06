import { api } from "./client";
import type { Paginated, Skill, SkillDetail } from "./types";

export async function fetchSkills(params?: { status?: string; page?: number; page_size?: number }) {
  return api.get<Paginated<Skill>>("/skills", { params });
}

export async function fetchSkillDetail(id: string) {
  return api.get<SkillDetail>(`/skills/${id}`);
}

export async function uploadSkill(form: FormData) {
  return api.post<Skill>("/skills/upload", form);
}

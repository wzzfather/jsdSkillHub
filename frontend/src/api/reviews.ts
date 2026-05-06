import { api } from "./client";
import type { ReviewPendingItem } from "./types";

export async function fetchPendingReviews() {
  return api.get<ReviewPendingItem[]>("/reviews");
}

export async function approveSkill(skillId: string, comment?: string) {
  return api.post<{ message: string }>(`/reviews/${skillId}/approve`, { comment });
}

export async function rejectSkill(skillId: string, comment?: string) {
  return api.post<{ message: string }>(`/reviews/${skillId}/reject`, { comment });
}

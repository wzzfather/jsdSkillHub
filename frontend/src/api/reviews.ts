import { api } from "./client";
import type { ReviewPendingItem, ReviewSourceStats } from "./types";

export async function fetchPendingReviews() {
  return api.get<ReviewPendingItem[]>("/reviews");
}

export async function fetchReviewSourceStats() {
  return api.get<ReviewSourceStats>("/reviews/source-stats");
}

export async function approveSkill(skillId: string, comment?: string) {
  return api.post<{ message: string }>(`/reviews/${skillId}/approve`, { comment });
}

export async function rejectSkill(skillId: string, comment?: string) {
  return api.post<{ message: string }>(`/reviews/${skillId}/reject`, { comment });
}

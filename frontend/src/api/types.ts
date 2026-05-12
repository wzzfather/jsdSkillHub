export interface Skill {
  id: string;
  name: string;
  description: string | null;
  version: string;
  author_id: string | null;
  status: string;
  category: string | null;
  package_url: string | null;
  offline_comment: string | null;
  namespace: string | null;
  tags: string[] | null;
  homepage_url: string | null;
  repository_url: string | null;
  icon_url: string | null;
  status_message: string | null;
  deprecated_at: string | null;
  created_at: string;
}

export interface SkillVersion {
  version: string;
  package_url: string | null;
  changelog: string | null;
  created_at: string;
  created_by: string | null;
}

export interface ScanLayer {
  scan_type: string;
  passed: boolean;
  result: Record<string, unknown> | unknown[] | null;
  created_at?: string;
}

export interface SkillDetail extends Skill {
  scans: ScanLayer[];
}

export interface SkillAdmin extends Skill {
  author_username?: string | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DownloadResponse {
  download_url: string;
}

export interface ReviewPendingItem {
  skill: Skill;
  scans: ScanLayer[];
  source?: string | null;
  author_username?: string | null;
}

export interface ReviewSourceStats {
  new_upload: number;
  resubmit: number;
  republish: number;
}

export interface WorkflowStep {
  key: string;
  title: string;
  description: string;
  route: string;
}

export interface WorkflowOverview {
  total: number;
  scanning: number;
  pending_review: number;
  published: number;
  rejected: number;
}

export interface UserPublic {
  id: string;
  username: string;
  role: string;
  email: string | null;
  email_verified: boolean;
}

/** GET/PUT /api/auth/me 响应（ISO 8601 时间的 created_at） */
export interface UserMeResponse {
  username: string;
  email: string | null;
  email_verified: boolean;
  role: string;
  avatar_url: string | null;
  created_at: string;
}

export interface SendCodeResponse {
  message: string;
  code: string;
}

export interface ActionResponse {
  message: string;
  new_status: string;
}

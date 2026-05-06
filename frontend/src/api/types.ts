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
  created_at: string;
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

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DownloadResponse {
  download_url: string;
}

export interface InstallResponse {
  message: string;
  path: string;
}

export interface ReviewPendingItem {
  skill: Skill;
  scans: ScanLayer[];
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

export interface SendCodeResponse {
  message: string;
  code: string;
}

export interface ActionResponse {
  message: string;
  new_status: string;
}

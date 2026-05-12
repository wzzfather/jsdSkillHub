<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  CircleCheck,
  CircleClose,
  Loading,
  WarningFilled,
} from "@element-plus/icons-vue";
import { ElMessage, type InputInstance } from "element-plus";
import { downloadSkill, fetchSkillDetail, fetchSkillVersions } from "@/api/skills";
import type { ScanLayer, SkillDetail, SkillVersion } from "@/api/types";
import { useLocale } from "@/locales";

const props = defineProps<{ id: string }>();

const router = useRouter();
const { t } = useLocale();
const loading = ref(false);
const detail = ref<SkillDetail | null>(null);
const versions = ref<SkillVersion[]>([]);
const versionsLoading = ref(false);
const versionsLoadFailed = ref(false);
const cliInstallInputRef = ref<InputInstance>();

function skillDisplayTitle(skill: Pick<SkillDetail, "name" | "namespace">) {
  const ns = skill.namespace?.trim();
  return ns ? `${ns}/${skill.name}` : skill.name;
}

function formatTime(iso?: string | null) {
  if (!iso) return t("common.emDash");
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function statusLabel(status: string) {
  const keys: Record<string, string> = {
    scanning: "skillStatus.scanning",
    pending_review: "skillStatus.pending_review",
    published: "skillStatus.published",
    deprecated: "skillStatus.deprecated",
    rejected: "skillStatus.rejected",
    offline: "skillStatus.offline",
    draft: "skillStatus.draft",
  };
  const k = keys[status];
  return k ? t(k) : status;
}

/** 扫描层列表 */
const layers = computed(() => {
  const want = ["semgrep", "clamav", "llm"];
  const list = detail.value?.scans ?? [];
  return want.map((scanType) => {
    const hit = list.find((s) => s.scan_type === scanType);
    return { type: scanType, scan: hit as ScanLayer | undefined };
  });
});

/** CLI 安装命令 */
const cliInstallCommand = computed(() => {
  if (!detail.value || detail.value.status !== "published") return "";
  const name = detail.value.name.trim();
  return name ? `jsdhub install ${name}` : "jsdhub install";
});

async function copyCliInstallCommand() {
  const text = cliInstallCommand.value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success(t("detail.cliInstallCopied"));
  } catch {
    ElMessage.error(t("detail.cliInstallCopyFail"));
  }
}

function focusCliInstallInput() {
  cliInstallInputRef.value?.focus?.();
  cliInstallInputRef.value?.select?.();
}

function scanIcon(scan: ScanLayer | undefined, skillStatus: string) {
  if (!scan && skillStatus === "scanning") return "loading";
  if (!scan) return "warn";
  return scan.passed ? "ok" : "bad";
}

function scanTagLabel(scan: ScanLayer | undefined, skillStatus: string) {
  const kind = scan?.scan_type;
  if (kind === "semgrep") return t("detail.scanStatic");
  if (kind === "clamav") return t("detail.scanSecurity");
  if (kind === "llm") return t("detail.scanSmart");
  if (!scan && skillStatus === "scanning") return t("detail.scanStatic");
  return t("detail.scanStatic");
}

function scanTagType(scan: ScanLayer | undefined, skillStatus: string) {
  if (!scan && skillStatus === "scanning") return "info";
  if (!scan) return "info";
  return scan.passed ? "success" : "danger";
}

function apiErrorDetail(err: unknown): string {
  const e = err as { response?: { data?: { detail?: unknown } } };
  const d = e.response?.data?.detail;
  if (typeof d === "string") return d;
  if (d && typeof d === "object" && "detail" in d) {
    const inner = (d as { detail?: unknown }).detail;
    if (typeof inner === "string") return inner;
  }
  return t("detail.errOp");
}

async function onDownloadZip() {
  if (!detail.value) return;
  try {
    const { data } = await downloadSkill(detail.value.id);
    window.open(data.download_url, "_blank", "noopener,noreferrer");
  } catch (e) {
    ElMessage.error(apiErrorDetail(e));
  }
}

async function loadVersions() {
  versionsLoading.value = true;
  versionsLoadFailed.value = false;
  try {
    versions.value = await fetchSkillVersions(props.id);
  } catch {
    versions.value = [];
    versionsLoadFailed.value = true;
  } finally {
    versionsLoading.value = false;
  }
}

async function load() {
  loading.value = true;
  try {
    const { data } = await fetchSkillDetail(props.id);
    detail.value = data;
    void loadVersions();
  } catch {
    ElMessage.error(t("detail.errLoad"));
    detail.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div class="detail-page">
    <div v-if="loading" class="muted">{{ t("detail.loading") }}</div>

    <div v-else-if="!detail" class="empty-card card-panel">
      <p class="muted">{{ t("detail.empty") }}</p>
      <el-button class="mt" type="primary" @click="router.push({ name: 'explore' })">{{ t("detail.backMarket") }}</el-button>
    </div>

    <div v-else>
        <el-breadcrumb separator="/" class="crumb">
          <el-breadcrumb-item :to="{ name: 'explore' }">{{ t("detail.breadcrumbMarket") }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ skillDisplayTitle(detail) }}</el-breadcrumb-item>
        </el-breadcrumb>

        <section class="main-card card-panel">
          <div class="hero-row">
          <div class="skill-icon-wrap" aria-hidden="true">
            <img v-if="detail.icon_url" class="skill-icon-img" :src="detail.icon_url" alt="" />
            <div v-else class="skill-icon-ph">
              <svg class="skill-icon-svg" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M12 2l7 4v8l-7 4-7-4V6l7-4zm0 2.2L6.5 7.1v6.3L12 17l5.5-3.6V7.1L12 4.2z"
                  opacity="0.95"
                />
              </svg>
            </div>
          </div>
          <div class="title-block">
            <h1 class="title">{{ skillDisplayTitle(detail) }}</h1>
            <div class="title-tags">
              <el-tag v-for="row in layers" :key="row.type" size="small" :type="scanTagType(row.scan, detail.status)" effect="dark" class="scan-result-tag">
                <el-icon v-if="scanIcon(row.scan, detail.status) === 'loading'" class="scan-tag-icon spin"><Loading /></el-icon>
                <el-icon v-else-if="scanIcon(row.scan, detail.status) === 'ok'" class="scan-tag-icon"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanIcon(row.scan, detail.status) === 'bad'" class="scan-tag-icon"><CircleClose /></el-icon>
                <el-icon v-else class="scan-tag-icon"><WarningFilled /></el-icon>
                {{ scanTagLabel(row.scan, detail.status) }}
              </el-tag>
              <el-tag v-if="detail.status === 'deprecated'" effect="dark" type="warning">{{ t("detail.deprecatedBadge") }}</el-tag>
              <el-tag effect="light" type="info">{{ statusLabel(detail.status) }}</el-tag>
              <el-tag effect="plain" type="info">v{{ detail.version }}</el-tag>
              <el-tag v-if="detail.category" effect="plain" type="info">{{ detail.category }}</el-tag>
              <el-tag v-for="tag in detail.tags || []" :key="tag" effect="plain" type="success" size="small">{{ tag }}</el-tag>
            </div>
          </div>
          </div>

          <el-alert
          v-if="detail.status === 'deprecated'"
          class="deprecated-alert"
          type="warning"
          :closable="false"
          show-icon
          :title="t('detail.deprecatedNotice')"
          >
            <template v-if="detail.status_message">{{ detail.status_message }}</template>
          </el-alert>

          <div v-if="detail.homepage_url || detail.repository_url" class="link-row">
          <el-link v-if="detail.homepage_url" :href="detail.homepage_url" target="_blank" rel="noopener noreferrer" type="primary">
            {{ t("detail.linkHomepage") }}
          </el-link>
          <el-link
            v-if="detail.repository_url"
            :href="detail.repository_url"
            target="_blank"
            rel="noopener noreferrer"
            type="primary"
          >
            {{ t("detail.linkRepository") }}
          </el-link>
          </div>

          <p class="body">{{ detail.description || t("detail.noDesc") }}</p>

          <div class="meta-line muted">
          <span>{{ t("detail.author") }}{{ detail.author_id ? `…${detail.author_id.slice(-10)}` : t("common.emDash") }}</span>
          <span class="dot">·</span>
          <span>{{ t("detail.submittedAt") }}{{ formatTime(detail.created_at) }}</span>
          </div>

          <template v-if="detail.status === 'published'">
          <div class="actions">
            <el-button type="primary" size="large" class="act-pri" @click="onDownloadZip">{{ t("detail.dlZip") }}</el-button>
          </div>

          <div class="cli-install-block">
            <div class="cli-install-head muted">{{ t("detail.cliInstallTitle") }}</div>
            <el-input
              ref="cliInstallInputRef"
              class="cli-install-input"
              :model-value="cliInstallCommand"
              readonly
              @click="focusCliInstallInput"
            >
              <template #append>
                <el-button type="primary" plain class="cli-copy-btn" @click="copyCliInstallCommand">{{ t("detail.cliInstallCopy") }}</el-button>
              </template>
            </el-input>
          </div>
          </template>
        </section>

        <section class="versions-section">
          <h2 class="section-title">{{ t("detail.versionsTitle") }}</h2>
          <div v-if="versionsLoading" class="muted">{{ t("common.loading") }}</div>
          <el-alert v-else-if="versionsLoadFailed" type="info" :closable="false" show-icon class="versions-hint">
            {{ t("detail.versionsNeedLogin") }}
          </el-alert>
          <el-table v-else :data="versions" stripe class="versions-table" empty-text="—">
          <el-table-column prop="version" :label="t('detail.versionsColVersion')" width="110" />
          <el-table-column :label="t('detail.versionsColPackage')" min-width="140">
            <template #default="{ row }">
              <el-link v-if="row.package_url" :href="row.package_url" target="_blank" rel="noopener noreferrer" type="primary">
                {{ t("detail.versionsDownload") }}
              </el-link>
              <span v-else class="muted">{{ t("common.emDash") }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('detail.versionsColChangelog')" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.changelog || t("common.emDash") }}
            </template>
          </el-table-column>
          <el-table-column :label="t('detail.versionsColCreated')" min-width="168">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('detail.versionsColAuthor')" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <template v-if="row.created_by">
                {{ row.created_by.length <= 12 ? row.created_by : `…${row.created_by.slice(-10)}` }}
              </template>
              <span v-else class="muted">{{ t("common.emDash") }}</span>
            </template>
          </el-table-column>
          </el-table>
        </section>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.crumb {
  font-size: 13px;
}

.crumb :deep(.el-breadcrumb__inner) {
  font-weight: 500;
  color: var(--app-muted);
}

.crumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: var(--app-text);
  font-weight: 600;
}

.main-card {
  padding: 24px;
}

.hero-row {
  display: flex;
  gap: 18px;
  align-items: flex-start;
}

.skill-icon-wrap {
  flex-shrink: 0;
}

.skill-icon-img {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-card);
  object-fit: cover;
  border: 1px solid var(--app-border);
  background: var(--app-bg);
}

.skill-icon-ph {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-card);
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--app-text) 8%, transparent);
  border: 1px solid var(--app-border);
  color: var(--app-muted);
}

.skill-icon-svg {
  width: 36px;
  height: 36px;
}

.deprecated-alert {
  margin-top: 16px;
  border-radius: var(--radius-control);
}

.link-row {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.versions-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.versions-hint {
  border-radius: var(--radius-control);
}

.versions-table {
  border-radius: var(--radius-card);
  overflow: hidden;
  border: 1px solid var(--app-border);
}

.title-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text);
  line-height: 1.25;
}

.title-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.body {
  margin: 16px 0 0;
  line-height: 1.6;
  color: var(--app-text);
  font-size: 14px;
}

.meta-line {
  margin-top: 14px;
  font-size: 13px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.dot {
  opacity: 0.45;
}

.actions {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.cli-install-block {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cli-install-head {
  font-size: 13px;
  font-weight: 600;
}

.cli-install-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-control);
  background: color-mix(in srgb, var(--app-text) 7%, transparent);
  box-shadow: none;
  border: 1px solid var(--app-border-strong);
}

.cli-install-input :deep(.el-input__inner) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  letter-spacing: 0.02em;
  color: var(--app-text);
}

.cli-install-input :deep(.el-input-group__append) {
  background: var(--app-surface);
  border-left-color: var(--app-border-strong);
}

.cli-copy-btn {
  border-radius: 0 var(--radius-control) var(--radius-control) 0;
  font-weight: 600;
}

.act-pri {
  min-width: 120px;
  font-weight: 600;
  border-radius: var(--radius-control);
}

.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

.scan-result-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.scan-tag-icon {
  font-size: 12px;
}

.spin {
  color: var(--app-muted);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.mt {
  margin-top: 12px;
}

</style>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  CircleCheck,
  CircleClose,
  DArrowLeft,
  DArrowRight,
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
const asideExpanded = ref(false);
const asideTab = ref<"scan" | "flow">("scan");
const isNarrow = ref(false);

let viewportMql: MediaQueryList | null = null;

function syncNarrowLayout() {
  if (typeof window === "undefined") return;
  const narrow = window.matchMedia("(max-width: 767px)").matches;
  const wasNarrow = isNarrow.value;
  isNarrow.value = narrow;
  if (narrow) {
    asideExpanded.value = true;
  } else if (wasNarrow && !narrow) {
    asideExpanded.value = false;
  }
}

function onViewportChange() {
  syncNarrowLayout();
}

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

/** 详情页任务流转：每步附带状态文案（已完成 / 进行中 / 待处理） */
const detailFlow = computed(() => {
  const st = detail.value?.status ?? "";
  const UP = t("flow.stepUpload");
  const SC = t("flow.stepScan");
  const RV = t("flow.stepReview");
  const PB = t("flow.stepPublished");
  const titles = [UP, SC, RV, PB] as const;
  let rows: { title: string; stateLabel: string }[] = [
    { title: UP, stateLabel: t("flow.statePending") },
    { title: SC, stateLabel: t("flow.statePending") },
    { title: RV, stateLabel: t("flow.statePending") },
    { title: PB, stateLabel: t("flow.statePending") },
  ];
  let active = 0;
  let processStatus: "process" | "error" | "success" | "wait" | "finish" = "process";
  let footnote = "" as string;

  if (st === "scanning") {
    rows = [
      { title: UP, stateLabel: t("flow.stateDone") },
      { title: SC, stateLabel: t("flow.stateRunning") },
      { title: RV, stateLabel: t("flow.statePending") },
      { title: PB, stateLabel: t("flow.statePending") },
    ];
    active = 1;
  } else if (st === "pending_review") {
    rows = [
      { title: UP, stateLabel: t("flow.stateDone") },
      { title: SC, stateLabel: t("flow.stateDone") },
      { title: RV, stateLabel: t("flow.stateRunning") },
      { title: PB, stateLabel: t("flow.statePending") },
    ];
    active = 2;
  } else if (st === "rejected") {
    rows = [
      { title: UP, stateLabel: t("flow.stateDone") },
      { title: SC, stateLabel: t("flow.stateDone") },
      { title: RV, stateLabel: t("flow.stateRejectedLine") },
      { title: PB, stateLabel: t("flow.statePending") },
    ];
    active = 2;
    processStatus = "error";
    footnote = t("flow.noteRejected");
  } else if (st === "published") {
    rows = titles.map((x) => ({ title: x, stateLabel: t("flow.stateDone") }));
    active = 4;
    processStatus = "success";
  } else if (st === "deprecated") {
    rows = titles.map((x) => ({ title: x, stateLabel: t("flow.stateDone") }));
    active = 4;
    processStatus = "success";
    footnote = t("flow.noteDeprecated");
  } else if (st === "offline") {
    rows = titles.map((x) => ({ title: x, stateLabel: t("flow.stateDone") }));
    active = 4;
    processStatus = "success";
    footnote = t("flow.noteOffline");
  } else {
    rows = [{ title: UP, stateLabel: t("flow.stateRunning") }, ...titles.slice(1).map((x) => ({ title: x, stateLabel: t("flow.statePending") }))];
    active = 0;
  }

  return { rows, active, processStatus, footnote };
});

const layers = computed(() => {
  const want = ["semgrep", "clamav", "llm"];
  const list = detail.value?.scans ?? [];
  return want.map((scanType) => {
    const hit = list.find((s) => s.scan_type === scanType);
    return { type: scanType, scan: hit as ScanLayer | undefined };
  });
});

/** 已上架 Skill 在终端通过 skillhub CLI 安装的完整命令（名称来自 API） */
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

function scanLayerTitle(scanType: string) {
  if (scanType === "semgrep") return t("detail.layerSemgrep");
  if (scanType === "clamav") return t("detail.layerClamav");
  return t("detail.layerLlm");
}

function scanIcon(scan: ScanLayer | undefined, skillStatus: string) {
  if (!scan && skillStatus === "scanning") return "loading";
  if (!scan) return "warn";
  return scan.passed ? "ok" : "bad";
}

function scanTone(kind: string) {
  if (kind === "semgrep") return "tone-semgrep";
  if (kind === "clamav") return "tone-clamav";
  return "tone-llm";
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

onMounted(() => {
  syncNarrowLayout();
  viewportMql = window.matchMedia("(max-width: 767px)");
  viewportMql.addEventListener("change", onViewportChange);
  void load();
});

onUnmounted(() => {
  viewportMql?.removeEventListener("change", onViewportChange);
});
</script>

<template>
  <div class="detail-page">
    <div v-if="loading" class="muted">{{ t("detail.loading") }}</div>

    <div v-else-if="!detail" class="empty-card card-panel">
      <p class="muted">{{ t("detail.empty") }}</p>
      <el-button class="mt" type="primary" @click="router.push({ name: 'explore' })">{{ t("detail.backMarket") }}</el-button>
    </div>

    <div v-else class="detail-layout">
      <div class="detail-main">
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

        <button
          type="button"
          class="aside-toggle"
          @click="asideExpanded = true"
          v-if="!isNarrow && !asideExpanded"
        >
          <el-icon><DArrowLeft /></el-icon>
          {{ t("detail.asideExpand") }}
        </button>
      </div>

      <aside class="detail-aside" :class="{ collapsed: !asideExpanded }">
        <div class="detail-aside-inner">
          <header class="aside-head">
            <span class="aside-head-title">{{ t("detail.scanTitle") }} & {{ t("detail.flowTitle") }}</span>
            <button
              type="button"
              class="aside-collapse-btn"
              v-if="!isNarrow"
              @click="asideExpanded = false"
            >
              <el-icon><DArrowRight /></el-icon>
              {{ t("detail.asideCollapse") }}
            </button>
          </header>
          <el-tabs v-model="asideTab" class="aside-tabs">
            <el-tab-pane :label="t('detail.scanTitle')" name="scan">
              <section class="scan-section">
                <el-row :gutter="16">
                  <el-col v-for="row in layers" :key="row.type" :xs="24" :md="8">
                    <div class="scan-card" :class="scanTone(row.type)">
                      <div class="scan-ico" aria-hidden="true">
                        <el-icon v-if="scanIcon(row.scan, detail.status) === 'loading'" class="spin"><Loading /></el-icon>
                        <el-icon v-else-if="scanIcon(row.scan, detail.status) === 'ok'" class="ico-ok"><CircleCheck /></el-icon>
                        <el-icon v-else-if="scanIcon(row.scan, detail.status) === 'bad'" class="ico-bad"><CircleClose /></el-icon>
                        <el-icon v-else class="ico-warn"><WarningFilled /></el-icon>
                      </div>
                      <div class="scan-info">
                        <div class="scan-name">{{ scanLayerTitle(row.type) }}</div>
                        <div class="scan-badge">
                          <template v-if="scanIcon(row.scan, detail.status) === 'loading'">
                            <el-tag type="info" effect="plain" size="small">{{ t("detail.tagPendingScan") }}</el-tag>
                          </template>
                          <template v-else-if="scanIcon(row.scan, detail.status) === 'warn'">
                            <el-tag type="info" effect="plain" size="small">N/A</el-tag>
                          </template>
                          <template v-else-if="row.scan?.passed">
                            <el-tag type="success" effect="dark" size="small">PASS</el-tag>
                          </template>
                          <template v-else>
                            <el-tag type="danger" effect="dark" size="small">FAIL</el-tag>
                          </template>
                        </div>
                      </div>
                    </div>
                  </el-col>
                </el-row>
              </section>
            </el-tab-pane>
            <el-tab-pane :label="t('detail.flowTitle')" name="flow">
              <section class="flow-section">
                <el-steps class="flow-steps" :active="detailFlow.active" finish-status="success" :process-status="detailFlow.processStatus" align-center>
                  <el-step v-for="(r, idx) in detailFlow.rows" :key="idx" :title="r.title" :description="r.stateLabel" />
                </el-steps>
                <el-alert v-if="detailFlow.footnote" class="flow-note" type="info" :closable="false" show-icon>
                  {{ detailFlow.footnote }}
                </el-alert>
              </section>
            </el-tab-pane>
          </el-tabs>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.detail-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-aside {
  width: 380px;
  flex-shrink: 0;
  transition:
    width 0.3s ease,
    opacity 0.3s ease;
  overflow: hidden;
}

.detail-aside.collapsed {
  width: 0;
  opacity: 0;
}

.detail-aside-inner {
  width: 380px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.aside-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.aside-head-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  line-height: 1.3;
  min-width: 0;
}

.aside-collapse-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-muted);
  background: var(--app-surface);
  border: 1px solid var(--app-border-strong);
  border-radius: var(--radius-control);
  cursor: pointer;
}

.aside-collapse-btn:hover {
  color: var(--app-text);
  border-color: var(--app-border-strong);
}

.aside-tabs :deep(.el-tabs__header) {
  margin-bottom: 12px;
}

.aside-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
  background: var(--app-surface);
  border: 1px solid var(--app-border-strong);
  border-radius: var(--radius-control);
  cursor: pointer;
  box-shadow: var(--shadow-card);
}

.aside-toggle:hover {
  border-color: color-mix(in srgb, var(--app-text) 28%, var(--app-border-strong));
}

@media (max-width: 767px) {
  .detail-layout {
    flex-direction: column;
  }

  .detail-aside {
    width: 100% !important;
    opacity: 1 !important;
  }

  .detail-aside-inner {
    width: 100%;
  }
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

.scan-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--app-surface);
  border-radius: var(--radius-control);
  padding: 16px;
  border: 1px solid var(--app-border);
  box-shadow: var(--shadow-card);
  border-left-width: 4px;
  height: 100%;
  box-sizing: border-box;
}

.tone-semgrep {
  border-left-color: #6366f1;
}

.tone-clamav {
  border-left-color: #22c55e;
}

.tone-llm {
  border-left-color: #3b82f6;
}

.scan-ico {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--app-text) 6%, transparent);
  font-size: 22px;
  flex-shrink: 0;
}

.scan-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.scan-name {
  font-weight: 600;
  color: var(--app-text);
  font-size: 14px;
}

.scan-badge {
  display: flex;
  align-items: center;
}

.ico-ok {
  color: var(--app-success);
}

.ico-bad {
  color: var(--app-danger);
}

.ico-warn {
  color: var(--app-warning);
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

.empty-card {
  text-align: left;
}

.mt {
  margin-top: 12px;
}

.flow-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.flow-steps {
  padding: 8px 0;
  background: var(--app-surface);
  border-radius: var(--radius-card);
  border: 1px solid var(--app-border);
  padding-left: 12px;
  padding-right: 12px;
}

.flow-steps :deep(.el-step__title) {
  font-size: 13px;
  font-weight: 600;
}

.flow-steps :deep(.el-step__description) {
  font-size: 12px;
  max-width: 160px;
  line-height: 1.4;
}

.flow-note {
  border-radius: var(--radius-control);
  background: var(--app-bg) !important;
  border: 1px solid var(--app-border-strong) !important;
  color: var(--app-muted) !important;
}

.flow-note :deep(.el-alert__title) {
  color: var(--app-muted);
  font-weight: 500;
}
</style>

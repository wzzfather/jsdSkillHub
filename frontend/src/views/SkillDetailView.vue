<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { CircleCheck, CircleClose, Loading, WarningFilled } from "@element-plus/icons-vue";
import { ElMessage, type InputInstance } from "element-plus";
import { downloadSkill, fetchSkillDetail } from "@/api/skills";
import type { ScanLayer, SkillDetail } from "@/api/types";
import { useLocale } from "@/locales";

const props = defineProps<{ id: string }>();

const router = useRouter();
const { t } = useLocale();
const loading = ref(false);
const detail = ref<SkillDetail | null>(null);
const cliInstallInputRef = ref<InputInstance>();

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
  return name ? `skillhub install ${name}` : "skillhub install";
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

async function load() {
  loading.value = true;
  try {
    const { data } = await fetchSkillDetail(props.id);
    detail.value = data;
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

    <div v-else class="stack">
      <el-breadcrumb separator="/" class="crumb">
        <el-breadcrumb-item :to="{ name: 'explore' }">{{ t("detail.breadcrumbMarket") }}</el-breadcrumb-item>
        <el-breadcrumb-item>{{ detail.name }}</el-breadcrumb-item>
      </el-breadcrumb>

      <section class="main-card card-panel">
        <div class="title-block">
          <h1 class="title">{{ detail.name }}</h1>
          <div class="title-tags">
            <el-tag effect="light" type="info">{{ statusLabel(detail.status) }}</el-tag>
            <el-tag effect="plain" type="info">v{{ detail.version }}</el-tag>
            <el-tag v-if="detail.category" effect="plain" type="info">{{ detail.category }}</el-tag>
          </div>
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

      <section class="scan-section">
        <h2 class="section-title">{{ t("detail.scanTitle") }}</h2>
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

      <section class="flow-section">
        <h2 class="section-title">{{ t("detail.flowTitle") }}</h2>
        <el-steps class="flow-steps" :active="detailFlow.active" finish-status="success" :process-status="detailFlow.processStatus" align-center>
          <el-step v-for="(r, idx) in detailFlow.rows" :key="idx" :title="r.title" :description="r.stateLabel" />
        </el-steps>
        <el-alert v-if="detailFlow.footnote" class="flow-note" type="info" :closable="false" show-icon>
          {{ detailFlow.footnote }}
        </el-alert>
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

.stack {
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

.title-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
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

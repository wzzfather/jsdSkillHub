<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchMySkills, resubmitSkill } from "@/api/skills";
import type { Skill } from "@/api/types";
import { useLocale } from "@/locales";

const router = useRouter();
const { t } = useLocale();
const loading = ref(false);
const items = ref<Skill[]>([]);
const resubmitingId = ref<string | null>(null);

function statusType(status: string) {
  const m: Record<string, string> = {
    scanning: "",
    pending_review: "warning",
    published: "success",
    rejected: "danger",
    offline: "info",
  };
  return (m[status] ?? "info") as "" | "success" | "warning" | "danger" | "info";
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

function rowClass({ row }: { row: Skill }) {
  return row.status === "rejected" ? "row-rejected" : "";
}

const waitingStatuses = computed(() => new Set(["scanning", "pending_review"]));

/** 列表页聚合「当前最关心」的流转位置：优先扫描中 → 待审批/驳回 → 已上架链路 */
const flowBar = computed(() => {
  const list = items.value;
  let activeStep = 0;
  let processStatus: "process" | "error" | "finish" | "success" | "wait" = "process";
  let bannerVariant: "none" | "rejected" | "offline" = "none";

  if (list.length === 0) {
    return { activeStep: 0, processStatus: "process" as const, bannerVariant: "none" as const };
  }

  const hasScanning = list.some((s) => s.status === "scanning");
  const hasPending = list.some((s) => s.status === "pending_review");
  const hasRejected = list.some((s) => s.status === "rejected");

  if (hasScanning) {
    activeStep = 1;
    processStatus = "process";
  } else if (hasPending || hasRejected) {
    activeStep = 2;
    processStatus = hasRejected ? "error" : "process";
    if (hasRejected) bannerVariant = "rejected";
  } else {
    activeStep = 4;
    processStatus = "success";
    if (list.some((s) => s.status === "offline")) bannerVariant = "offline";
  }

  return { activeStep, processStatus, bannerVariant };
});

const livePipelineHint = computed(() => {
  return items.value.filter((s) => s.status === "scanning" || s.status === "pending_review");
});

let pollTimer: ReturnType<typeof setInterval> | undefined;

function clearPoll() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = undefined;
}

function restartPollIfNeeded() {
  clearPoll();
  const needPoll = items.value.some((s) => s.status === "scanning" || s.status === "pending_review");
  if (!needPoll) return;
  pollTimer = window.setInterval(() => void loadQuiet(), 3000);
}

async function loadQuiet() {
  try {
    const all: Skill[] = [];
    let p = 1;
    while (true) {
      const { data } = await fetchMySkills({ page: p, page_size: 100 });
      all.push(...data.items);
      if (data.items.length === 0 || all.length >= data.total) break;
      p += 1;
    }
    items.value = all;
    restartPollIfNeeded();
  } catch {
    /* 轮询失败时静默 */
  }
}

async function load() {
  loading.value = true;
  try {
    const all: Skill[] = [];
    let p = 1;
    while (true) {
      const { data } = await fetchMySkills({ page: p, page_size: 100 });
      all.push(...data.items);
      if (data.items.length === 0 || all.length >= data.total) break;
      p += 1;
    }
    items.value = all;
    restartPollIfNeeded();
  } catch {
    ElMessage.error(t("myApps.errLoad"));
  } finally {
    loading.value = false;
  }
}

function goDetail(s: Skill) {
  router.push({ name: "skill-detail", params: { id: s.id } });
}

async function onResubmit(s: Skill) {
  resubmitingId.value = s.id;
  try {
    await resubmitSkill(s.id);
    ElMessage.success(t("myApps.msgResubmitOk"));
    await load();
  } catch {
    ElMessage.error(t("myApps.errResubmit"));
  } finally {
    resubmitingId.value = null;
  }
}

onMounted(() => void load());
onUnmounted(() => clearPoll());
</script>

<template>
  <div class="my-apps">
    <header class="page-head card-panel">
      <h2 class="page-heading">{{ t("myApps.title") }}</h2>
      <p class="muted page-lead">{{ t("myApps.lead") }}</p>

      <div class="flow-wrap">
        <el-steps class="lifecycle-steps" :active="flowBar.activeStep" finish-status="success" :process-status="flowBar.processStatus" align-center>
          <el-step :title="t('myApps.flowUpload')" :description="t('myApps.flowUploadDesc')" />
          <el-step :title="t('myApps.flowScan')" :description="t('myApps.flowScanDesc')" />
          <el-step :title="t('myApps.flowReview')" :description="t('myApps.flowReviewDesc')" />
          <el-step :title="t('myApps.flowPub')" :description="t('myApps.flowPubDesc')" />
        </el-steps>

        <el-alert v-if="flowBar.bannerVariant === 'rejected'" class="flow-banner flow-banner-danger" type="error" :closable="false" show-icon :title="t('myApps.bannerRejected')" />
        <el-alert v-else-if="flowBar.bannerVariant === 'offline'" class="flow-banner flow-banner-muted" type="info" :closable="false" show-icon :title="t('myApps.bannerOffline')" />

        <div v-if="livePipelineHint.length" class="live-hint card-panel-muted">
          <div class="live-hint-title">{{ t("myApps.inProgress") }}</div>
          <ul class="live-hint-list">
            <li v-for="s in livePipelineHint" :key="s.id" class="live-hint-item">
              <span class="live-hint-name">{{ s.name }}</span>
              <span class="muted">{{ statusLabel(s.status) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </header>

    <div v-if="loading" class="muted" style="padding: 16px 4px">{{ t("common.loading") }}</div>

    <el-empty v-else-if="items.length === 0" :description="t('myApps.empty')" />

    <el-card v-else class="table-card" shadow="never">
      <el-table :data="items" stripe class="apps-table" :row-class-name="rowClass" style="width: 100%">
        <el-table-column prop="name" :label="t('myApps.colName')" min-width="200">
          <template #default="{ row }">
            <span class="link" @click="goDetail(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="version" :label="t('myApps.colVersion')" width="100" />
        <el-table-column prop="category" :label="t('myApps.colCategory')" width="140">
          <template #default="{ row }">
            {{ row.category || t("common.emDash") }}
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('myApps.colStatus')" min-width="200">
          <template #default="{ row }">
            <template v-if="waitingStatuses.has(row.status)">
              <el-tag type="warning" size="small">{{ t("myApps.tagWaiting") }}</el-tag>
              <span class="muted wait-hint">{{ statusLabel(row.status) }}</span>
            </template>
            <template v-else-if="row.status === 'offline'">
              <el-tag type="info" size="small">{{ t("myApps.tagOffline") }}</el-tag>
              <div v-if="row.offline_comment" class="offline-reason muted">
                {{ t("myApps.offlineReason") }}{{ row.offline_comment }}
              </div>
            </template>
            <el-tag v-else :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('myApps.colActions')" width="140">
          <template #default="{ row }">
            <template v-if="row.status === 'published'">
              <el-button text type="primary" size="small" @click="goDetail(row)">{{ t("myApps.actionView") }}</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-button text type="primary" size="small" :loading="resubmitingId === row.id" @click="onResubmit(row)">
                {{ t("myApps.actionResubmit") }}
              </el-button>
            </template>
            <template v-else-if="!waitingStatuses.has(row.status) && row.status !== 'offline'">
              <el-button text type="primary" size="small" @click="goDetail(row)">{{ t("myApps.actionDetail") }}</el-button>
            </template>
            <span v-else class="muted">{{ t("common.emDash") }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.my-apps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-head {
  padding: 24px;
}

.page-heading {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 800;
}

.page-lead {
  margin: 0 0 16px;
}

.flow-wrap {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.lifecycle-steps {
  padding: 8px 0 4px;
}

.lifecycle-steps :deep(.el-step__title) {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
}

.lifecycle-steps :deep(.el-step__description) {
  font-size: 12px;
  color: var(--app-muted);
}

.flow-banner {
  border-radius: var(--radius-control);
}

.flow-banner-muted {
  background: var(--app-bg) !important;
  border: 1px solid var(--app-border-strong) !important;
  color: var(--app-muted) !important;
}

.flow-banner-muted :deep(.el-alert__title) {
  color: var(--app-muted);
}

.card-panel-muted {
  background: var(--app-bg);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-control);
  padding: 14px 16px;
}

.live-hint-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text);
  margin-bottom: 8px;
}

.live-hint-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.live-hint-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.live-hint-name {
  font-weight: 600;
  color: var(--app-text);
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.apps-table :deep(.cell) {
  padding-top: 14px;
  padding-bottom: 14px;
}

.apps-table :deep(tr.row-rejected > td:first-child) {
  box-shadow: inset 4px 0 0 rgba(245, 158, 11, 0.45);
}

.link {
  color: var(--app-text);
  cursor: pointer;
  font-weight: 600;
}

.link:hover {
  color: var(--app-primary-deep);
  text-decoration: underline;
}

.wait-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
}

.offline-reason {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.45;
  max-width: 360px;
}
</style>

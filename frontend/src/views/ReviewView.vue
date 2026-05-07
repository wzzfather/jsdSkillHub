<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { CircleCheck, CircleClose } from "@element-plus/icons-vue";
import {
  approveSkill as approveSkillApi,
  fetchPendingReviews,
  fetchReviewSourceStats,
  rejectSkill as rejectSkillApi,
} from "@/api/reviews";
import type { ReviewPendingItem, ScanLayer } from "@/api/types";
import { useLocale } from "@/locales";

const { t } = useLocale();

const loading = ref(false);
const forbidden = ref(false);
const rows = ref<ReviewPendingItem[]>([]);

const sourceStats = reactive({
  new_upload: 0,
  resubmit: 0,
  republish: 0,
});

const drawer = ref(false);
const current = ref<ReviewPendingItem | null>(null);
const comment = ref("");

const pendingCount = computed(() => rows.value.length);

function formatTime(iso?: string | null) {
  if (!iso) return t("common.emDash");
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function pickScan(scans: ScanLayer[], type: "semgrep" | "clamav" | "llm") {
  return scans.find((s) => s.scan_type === type);
}

function scanCellState(scans: ScanLayer[], type: "semgrep" | "clamav" | "llm") {
  const s = pickScan(scans, type);
  if (!s) return "none" as const;
  return s.passed ? ("ok" as const) : ("bad" as const);
}

function scanLabel(scanType: string) {
  if (scanType === "semgrep") return t("review.scanType.semgrep");
  if (scanType === "clamav") return t("review.scanType.clamav");
  if (scanType === "llm") return t("review.scanType.llm");
  return scanType;
}

function sortedScans(scans: ScanLayer[]) {
  const order = ["semgrep", "clamav", "llm"];
  return [...scans].sort((a, b) => order.indexOf(a.scan_type) - order.indexOf(b.scan_type));
}

function findingsPreview(result: ScanLayer["result"]): unknown {
  if (result && typeof result === "object" && !Array.isArray(result) && "findings" in result) {
    return (result as { findings?: unknown }).findings ?? result;
  }
  return result;
}

function layerAccent(layerKey: string) {
  if (layerKey === "semgrep") return "accent-semgrep";
  if (layerKey === "clamav") return "accent-clamav";
  return "accent-llm";
}

function sourceLabel(src?: string | null) {
  if (src === "new_upload") return t("review.source.newUpload");
  if (src === "resubmit") return t("review.source.resubmit");
  if (src === "republish") return t("review.source.republish");
  return t("common.emDash");
}

function sourceTagType(src?: string | null): "info" | "warning" | "success" {
  if (src === "resubmit") return "warning";
  if (src === "republish") return "success";
  return "info";
}

async function reload() {
  loading.value = true;
  forbidden.value = false;
  try {
    const [listRes, statsRes] = await Promise.all([fetchPendingReviews(), fetchReviewSourceStats()]);
    rows.value = listRes.data;
    sourceStats.new_upload = statsRes.data.new_upload;
    sourceStats.resubmit = statsRes.data.resubmit;
    sourceStats.republish = statsRes.data.republish;
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } };
    if (err.response?.status === 403) forbidden.value = true;
    rows.value = [];
    sourceStats.new_upload = 0;
    sourceStats.resubmit = 0;
    sourceStats.republish = 0;
    ElMessage.error(t("review.loadFail"));
  } finally {
    loading.value = false;
  }
}

function openDetail(row: ReviewPendingItem) {
  current.value = row;
  comment.value = "";
  drawer.value = true;
}

function onRowClick(row: ReviewPendingItem) {
  openDetail(row);
}

async function approve() {
  if (!current.value) return;
  try {
    await ElMessageBox.confirm(t("review.approve.confirm"), t("review.approve.title"), {
      type: "warning",
      confirmButtonText: t("review.btn.approve"),
      cancelButtonText: t("review.btn.cancel"),
    });
    await approveSkillApi(current.value.skill.id, comment.value.trim() || undefined);
    ElMessage.success(t("review.approve.success"));
    drawer.value = false;
    await reload();
  } catch {
    /* cancel */
  }
}

async function reject() {
  if (!current.value) return;
  try {
    await ElMessageBox.confirm(t("review.reject.confirm"), t("review.reject.title"), {
      type: "warning",
      confirmButtonText: t("review.btn.reject"),
      cancelButtonText: t("review.btn.cancel"),
    });
    await rejectSkillApi(current.value.skill.id, comment.value.trim() || undefined);
    ElMessage.success(t("review.reject.success"));
    drawer.value = false;
    await reload();
  } catch {
    /* cancel */
  }
}

onMounted(() => void reload());
</script>

<template>
  <div class="review-page">
    <header class="page-head">
      <div class="head-copy">
        <h2 class="page-heading">{{ t("review.title") }}</h2>
        <p class="muted page-lead">{{ t("review.lead") }}</p>
      </div>
      <el-button type="primary" plain class="reload" @click="reload">{{ t("review.refresh") }}</el-button>
    </header>

    <el-alert
      v-if="forbidden"
      type="warning"
      show-icon
      :title="t('review.warn.noAdmin')"
      :description="t('review.warn.noAdminDesc')"
    />

    <el-row v-else class="stats" :gutter="16">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-kpi">{{ pendingCount }}</div>
          <div class="stat-label muted">{{ t("review.stat.pendingQueue") }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card stat-card-muted">
          <div class="stat-kpi">{{ sourceStats.new_upload }}</div>
          <div class="stat-label muted">{{ t("review.stat.newUpload") }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card stat-card-muted">
          <div class="stat-kpi">{{ sourceStats.resubmit }}</div>
          <div class="stat-label muted">{{ t("review.stat.resubmit") }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card stat-card-muted">
          <div class="stat-kpi">{{ sourceStats.republish }}</div>
          <div class="stat-label muted">{{ t("review.stat.republish") }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="!forbidden" class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="rows"
        stripe
        class="review-table"
        style="width: 100%"
        @row-click="onRowClick"
      >
        <el-table-column :label="t('review.col.name')" min-width="180">
          <template #default="{ row }">{{ row.skill.name }}</template>
        </el-table-column>
        <el-table-column :label="t('review.col.version')" width="110">
          <template #default="{ row }">{{ row.skill.version }}</template>
        </el-table-column>
        <el-table-column :label="t('review.col.category')" width="120">
          <template #default="{ row }">{{ row.skill.category || t("common.emDash") }}</template>
        </el-table-column>
        <el-table-column :label="t('review.col.source')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.source" size="small" :type="sourceTagType(row.source)">{{ sourceLabel(row.source) }}</el-tag>
            <span v-else class="muted">{{ t("common.emDash") }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('review.col.submitter')" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="muted">{{ row.author_username || t("common.emDash") }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('review.col.scanSummary')" min-width="220">
          <template #default="{ row }">
            <div class="icons">
              <span class="ico" title="Semgrep">
                <el-icon v-if="scanCellState(row.scans, 'semgrep') === 'ok'" class="ok"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanCellState(row.scans, 'semgrep') === 'bad'" class="bad"><CircleClose /></el-icon>
                <span v-else class="muted tiny">{{ t("common.emDash") }}</span>
              </span>
              <span class="ico" title="ClamAV">
                <el-icon v-if="scanCellState(row.scans, 'clamav') === 'ok'" class="ok"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanCellState(row.scans, 'clamav') === 'bad'" class="bad"><CircleClose /></el-icon>
                <span v-else class="muted tiny">{{ t("common.emDash") }}</span>
              </span>
              <span class="ico" title="LLM">
                <el-icon v-if="scanCellState(row.scans, 'llm') === 'ok'" class="ok"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanCellState(row.scans, 'llm') === 'bad'" class="bad"><CircleClose /></el-icon>
                <span v-else class="muted tiny">{{ t("common.emDash") }}</span>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="t('review.col.submitTime')" min-width="170">
          <template #default="{ row }">
            <span class="muted">{{ formatTime(row.skill.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('review.col.action')" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row)">{{ t("review.action.open") }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawer" size="560px" direction="rtl" :title="t('review.drawer.title')" class="review-drawer">
      <template v-if="current">
        <div class="detail-head">
          <div class="detail-title">{{ current.skill.name }}</div>
          <div class="muted detail-sub">
            v{{ current.skill.version }} · {{ current.skill.category || t("review.drawer.uncategorized") }}
          </div>
          <div class="detail-meta">
            <el-tag v-if="current.source" size="small" :type="sourceTagType(current.source)">{{ sourceLabel(current.source) }}</el-tag>
            <span class="detail-author muted">{{ t("review.drawer.submitter") }}{{ current.author_username || t("common.emDash") }}</span>
          </div>
        </div>

        <div v-for="s in sortedScans(current.scans)" :key="s.scan_type" class="scan-layer-card card-panel" :class="layerAccent(s.scan_type)">
          <div class="layer-head">
            <div>{{ scanLabel(s.scan_type) }}</div>
            <el-tag :type="s.passed ? 'success' : 'danger'" effect="dark">{{ s.passed ? t("status.passed") : t("status.notPassed") }}</el-tag>
          </div>
          <div class="sub muted">{{ t("review.findings") }}</div>
          <pre class="json">{{ JSON.stringify(findingsPreview(s.result), null, 2) }}</pre>
        </div>

        <div class="foot card-panel">
          <div class="sub">{{ t("review.notes") }}</div>
          <el-input v-model="comment" type="textarea" :rows="4" :placeholder="t('review.notesPlaceholder')" />
          <div class="actions">
            <el-button type="success" @click="approve">{{ t("review.btn.approve") }}</el-button>
            <el-button type="danger" plain @click="reject">{{ t("review.btn.reject") }}</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.review-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.page-heading {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 800;
}

.page-lead {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

.reload {
  border-radius: var(--radius-control);
}

.stats {
  margin-top: 2px;
}

.stat-card :deep(.el-card__body) {
  padding: 18px 16px;
}

.stat-card-muted :deep(.el-card__body) {
  background: var(--app-bg);
}

.stat-kpi {
  font-size: 30px;
  font-weight: 800;
  color: var(--app-text);
  line-height: 1.05;
}

.stat-label {
  margin-top: 6px;
  font-size: 13px;
  font-weight: 600;
}

.stat-hint {
  margin-top: 6px;
  font-size: 12px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.review-table {
  --table-pad-y: 14px;
}

.review-table :deep(.cell) {
  padding-top: var(--table-pad-y);
  padding-bottom: var(--table-pad-y);
}

.review-table :deep(.el-table__row) {
  cursor: pointer;
}

.icons {
  display: inline-flex;
  gap: 10px;
  align-items: center;
}

.ico {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
}

.tiny {
  font-size: 12px;
}

.ok {
  color: var(--app-success);
}

.bad {
  color: var(--app-danger);
}

.detail-head {
  margin-bottom: 12px;
}

.detail-title {
  font-size: 18px;
  font-weight: 800;
}

.detail-sub {
  margin-top: 4px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.detail-author {
  font-size: 13px;
}

.scan-layer-card {
  margin-bottom: 12px;
  padding: 16px !important;
  border-left-width: 4px;
}

.accent-semgrep {
  border-left-color: #6366f1;
}

.accent-clamav {
  border-left-color: #22c55e;
}

.accent-llm {
  border-left-color: #3b82f6;
}

.layer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-weight: 700;
}

.sub {
  font-size: 12px;
  margin-bottom: 8px;
}

.json {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  color: var(--app-text);
  background: var(--app-bg);
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 10px;
}

.foot {
  padding: 16px !important;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.review-drawer :deep(.el-drawer__body) {
  padding: 16px 18px 24px;
}
</style>

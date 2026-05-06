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
  if (!iso) return "—";
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

function scanLabel(t: string) {
  if (t === "semgrep") return "Semgrep 静态扫描";
  if (t === "clamav") return "ClamAV 恶意文件扫描";
  if (t === "llm") return "LLM 语义分析";
  return t;
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

function layerAccent(t: string) {
  if (t === "semgrep") return "accent-semgrep";
  if (t === "clamav") return "accent-clamav";
  return "accent-llm";
}

function sourceLabel(src?: string | null) {
  if (src === "new_upload") return "新上传";
  if (src === "resubmit") return "重新提交";
  if (src === "republish") return "重新上架";
  return "—";
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
    ElMessage.error("加载审批列表失败");
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
    await ElMessageBox.confirm("确认通过并上架该 Skill？", "审批确认", {
      type: "warning",
      confirmButtonText: "通过",
      cancelButtonText: "取消",
    });
    await approveSkillApi(current.value.skill.id, comment.value.trim() || undefined);
    ElMessage.success("已通过");
    drawer.value = false;
    await reload();
  } catch {
    /* cancel */
  }
}

async function reject() {
  if (!current.value) return;
  try {
    await ElMessageBox.confirm("确认驳回该 Skill？", "驳回确认", {
      type: "warning",
      confirmButtonText: "驳回",
      cancelButtonText: "取消",
    });
    await rejectSkillApi(current.value.skill.id, comment.value.trim() || undefined);
    ElMessage.success("已驳回");
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
        <h2 class="page-heading">审批工作台</h2>
        <p class="muted page-lead">管理员查看三层扫描结果并做出人工决策。</p>
      </div>
      <el-button type="primary" plain class="reload" @click="reload">刷新</el-button>
    </header>

    <el-alert v-if="forbidden" type="warning" show-icon title="需要管理员权限" description="请使用管理员账号登录后再访问。" />

    <el-row v-else class="stats" :gutter="16">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-kpi">{{ pendingCount }}</div>
          <div class="stat-label muted">待审批（当前队列）</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card stat-card-muted">
          <div class="stat-kpi">{{ sourceStats.new_upload }}</div>
          <div class="stat-label muted">新上传</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card stat-card-muted">
          <div class="stat-kpi">{{ sourceStats.resubmit }}</div>
          <div class="stat-label muted">重新提交</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="stat-card stat-card-muted">
          <div class="stat-kpi">{{ sourceStats.republish }}</div>
          <div class="stat-label muted">重新上架</div>
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
        <el-table-column label="名称" min-width="180">
          <template #default="{ row }">{{ row.skill.name }}</template>
        </el-table-column>
        <el-table-column label="版本" width="110">
          <template #default="{ row }">{{ row.skill.version }}</template>
        </el-table-column>
        <el-table-column label="分类" width="120">
          <template #default="{ row }">{{ row.skill.category || "—" }}</template>
        </el-table-column>
        <el-table-column label="来源" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.source" size="small" :type="sourceTagType(row.source)">{{ sourceLabel(row.source) }}</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="提交者" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="muted">{{ row.author_username || "—" }}</span>
          </template>
        </el-table-column>
        <el-table-column label="扫描摘要" min-width="220">
          <template #default="{ row }">
            <div class="icons">
              <span class="ico" title="Semgrep">
                <el-icon v-if="scanCellState(row.scans, 'semgrep') === 'ok'" class="ok"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanCellState(row.scans, 'semgrep') === 'bad'" class="bad"><CircleClose /></el-icon>
                <span v-else class="muted tiny">—</span>
              </span>
              <span class="ico" title="ClamAV">
                <el-icon v-if="scanCellState(row.scans, 'clamav') === 'ok'" class="ok"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanCellState(row.scans, 'clamav') === 'bad'" class="bad"><CircleClose /></el-icon>
                <span v-else class="muted tiny">—</span>
              </span>
              <span class="ico" title="LLM">
                <el-icon v-if="scanCellState(row.scans, 'llm') === 'ok'" class="ok"><CircleCheck /></el-icon>
                <el-icon v-else-if="scanCellState(row.scans, 'llm') === 'bad'" class="bad"><CircleClose /></el-icon>
                <span v-else class="muted tiny">—</span>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="170">
          <template #default="{ row }">
            <span class="muted">{{ formatTime(row.skill.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row)">打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawer" size="560px" direction="rtl" title="审批详情" class="review-drawer">
      <template v-if="current">
        <div class="detail-head">
          <div class="detail-title">{{ current.skill.name }}</div>
          <div class="muted detail-sub">v{{ current.skill.version }} · {{ current.skill.category || "未分类" }}</div>
          <div class="detail-meta">
            <el-tag v-if="current.source" size="small" :type="sourceTagType(current.source)">{{ sourceLabel(current.source) }}</el-tag>
            <span class="detail-author muted">提交者：{{ current.author_username || "—" }}</span>
          </div>
        </div>

        <div v-for="s in sortedScans(current.scans)" :key="s.scan_type" class="scan-layer-card card-panel" :class="layerAccent(s.scan_type)">
          <div class="layer-head">
            <div>{{ scanLabel(s.scan_type) }}</div>
            <el-tag :type="s.passed ? 'success' : 'danger'" effect="dark">{{ s.passed ? "通过" : "不通过" }}</el-tag>
          </div>
          <div class="sub muted">告警详情（findings）</div>
          <pre class="json">{{ JSON.stringify(findingsPreview(s.result), null, 2) }}</pre>
        </div>

        <div class="foot card-panel">
          <div class="sub">备注（可选）</div>
          <el-input v-model="comment" type="textarea" :rows="4" placeholder="审批意见将会记录在后端审计信息中（若接口支持）" />
          <div class="actions">
            <el-button type="success" @click="approve">通过</el-button>
            <el-button type="danger" plain @click="reject">驳回</el-button>
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

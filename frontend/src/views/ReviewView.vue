<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { CircleCheck, CircleClose } from "@element-plus/icons-vue";
import { approveSkill as approveSkillApi, fetchPendingReviews, rejectSkill as rejectSkillApi } from "@/api/reviews";
import type { ReviewPendingItem, ScanLayer, Skill } from "@/api/types";

const loading = ref(false);
const forbidden = ref(false);
const rows = ref<ReviewPendingItem[]>([]);

const drawer = ref(false);
const current = ref<ReviewPendingItem | null>(null);
const comment = ref("");

const tableRows = computed(() => rows.value.map((r) => r.skill));

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

async function reload() {
  loading.value = true;
  forbidden.value = false;
  try {
    const { data } = await fetchPendingReviews();
    rows.value = data;
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } };
    if (err.response?.status === 403) forbidden.value = true;
    ElMessage.error("加载审批列表失败");
  } finally {
    loading.value = false;
  }
}

function openDetail(row: Skill) {
  const hit = rows.value.find((r) => r.skill.id === row.id);
  current.value = hit || null;
  comment.value = "";
  drawer.value = true;
}

function onRowClick(row: Skill) {
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
  <div class="card-panel">
    <div class="header-row">
      <div>
        <h2 class="page-title">审批工作台</h2>
        <p class="muted">管理员查看三层扫描结果并做出人工决策。</p>
      </div>
      <el-button type="primary" plain @click="reload">刷新</el-button>
    </div>

    <el-alert v-if="forbidden" type="warning" show-icon title="需要管理员权限" description="请使用管理员账号登录后再访问。" />

    <el-table v-loading="loading" :data="tableRows" class="mt" style="width: 100%" @row-click="onRowClick">
      <el-table-column prop="name" label="名称" min-width="200" />
      <el-table-column prop="version" label="版本" width="110" />
      <el-table-column prop="category" label="分类" width="140">
        <template #default="{ row }">{{ row.category || "—" }}</template>
      </el-table-column>
      <el-table-column label="扫描摘要" min-width="220">
        <template #default="{ row }">
          <div class="icons">
            <span class="ico" title="Semgrep">
              <el-icon v-if="scanCellState(rows.find((r) => r.skill.id === row.id)?.scans || [], 'semgrep') === 'ok'" class="ok"
                ><CircleCheck
              /></el-icon>
              <el-icon
                v-else-if="scanCellState(rows.find((r) => r.skill.id === row.id)?.scans || [], 'semgrep') === 'bad'"
                class="bad"
                ><CircleClose
              /></el-icon>
              <span v-else class="muted tiny">—</span>
            </span>
            <span class="ico" title="ClamAV">
              <el-icon v-if="scanCellState(rows.find((r) => r.skill.id === row.id)?.scans || [], 'clamav') === 'ok'" class="ok"
                ><CircleCheck
              /></el-icon>
              <el-icon
                v-else-if="scanCellState(rows.find((r) => r.skill.id === row.id)?.scans || [], 'clamav') === 'bad'"
                class="bad"
                ><CircleClose
              /></el-icon>
              <span v-else class="muted tiny">—</span>
            </span>
            <span class="ico" title="LLM">
              <el-icon v-if="scanCellState(rows.find((r) => r.skill.id === row.id)?.scans || [], 'llm') === 'ok'" class="ok"
                ><CircleCheck
              /></el-icon>
              <el-icon
                v-else-if="scanCellState(rows.find((r) => r.skill.id === row.id)?.scans || [], 'llm') === 'bad'"
                class="bad"
                ><CircleClose
              /></el-icon>
              <span v-else class="muted tiny">—</span>
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="提交时间" min-width="170">
        <template #default="{ row }">
          <span class="muted">{{ formatTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="openDetail(row)">打开</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="drawer" size="560px" direction="rtl" title="审批详情">
      <template v-if="current">
        <div class="detail-head">
          <div class="detail-title">{{ current.skill.name }}</div>
          <div class="muted">v{{ current.skill.version }} · {{ current.skill.category || "未分类" }}</div>
        </div>

        <div v-for="s in sortedScans(current.scans)" :key="s.scan_type" class="layer card-panel">
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
.header-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.mt {
  margin-top: 16px;
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
  color: #22c55e;
}

.bad {
  color: #e74c3c;
}

.detail-head {
  margin-bottom: 12px;
}

.detail-title {
  font-size: 18px;
  font-weight: 700;
}

.layer {
  margin-bottom: 12px;
  padding: 16px;
}

.layer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-weight: 600;
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
  background: #fafafa;
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 10px;
}

.foot {
  padding: 16px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { CircleCheck, CircleClose, Loading, WarningFilled } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { downloadSkill, fetchSkillDetail, installSkill } from "@/api/skills";
import type { ScanLayer, SkillDetail } from "@/api/types";

const props = defineProps<{ id: string }>();

const router = useRouter();
const loading = ref(false);
const installing = ref(false);
const detail = ref<SkillDetail | null>(null);

function formatTime(iso?: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function statusLabel(status: string) {
  const m: Record<string, string> = {
    scanning: "扫描中",
    pending_review: "待审批",
    published: "已上架",
    rejected: "已驳回",
  };
  return m[status] ?? status;
}

const layers = computed(() => {
  const want = ["semgrep", "clamav", "llm"];
  const list = detail.value?.scans ?? [];
  return want.map((t) => {
    const hit = list.find((s) => s.scan_type === t);
    return { type: t, scan: hit as ScanLayer | undefined };
  });
});

function layerTitle(t: string) {
  if (t === "semgrep") return "Semgrep 静态扫描";
  if (t === "clamav") return "ClamAV 恶意文件扫描";
  return "LLM 语义分析";
}

function scanIcon(scan: ScanLayer | undefined, skillStatus: string) {
  if (!scan && skillStatus === "scanning") return "loading";
  if (!scan) return "warn";
  return scan.passed ? "ok" : "bad";
}

function apiErrorDetail(err: unknown): string {
  const e = err as { response?: { data?: { detail?: unknown } } };
  const d = e.response?.data?.detail;
  if (typeof d === "string") return d;
  if (d && typeof d === "object" && "detail" in d) {
    const inner = (d as { detail?: unknown }).detail;
    if (typeof inner === "string") return inner;
  }
  return "操作失败";
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

async function onInstallOpenClaw() {
  if (!detail.value) return;
  try {
    await ElMessageBox.confirm(
      "将把 Skill 安装到本机 OpenClaw 目录（已存在同名目录会先备份再覆盖）。是否继续？",
      "安装到 OpenClaw",
      {
        type: "warning",
        confirmButtonText: "安装",
        cancelButtonText: "取消",
      },
    );
  } catch {
    return;
  }
  installing.value = true;
  try {
    const { data } = await installSkill(detail.value.id);
    ElMessage.success(`${data.message}：${data.path}`);
  } catch (e) {
    ElMessage.error(apiErrorDetail(e));
  } finally {
    installing.value = false;
  }
}

async function load() {
  loading.value = true;
  try {
    const { data } = await fetchSkillDetail(props.id);
    detail.value = data;
  } catch {
    ElMessage.error("无法加载详情（可能没有权限或未登录）");
    detail.value = null;
  } finally {
    loading.value = false;
  }
}

function text(key: string) {
  const map: Record<string, string> = {
    loading: "加载中…",
    back: "返回市场",
    meta: "元信息",
    desc: "描述",
    scanSum: "扫描结果摘要",
    dlZip: "下载 zip",
    installOc: "安装到 OpenClaw",
  };
  return map[key] ?? key;
}

onMounted(() => void load());
</script>

<template>
  <div class="detail-page">
    <div class="topbar">
      <el-button class="neutral" plain @click="router.push({ name: 'explore' })">{{ text("back") }}</el-button>
    </div>

    <div v-if="loading" class="muted">{{ text("loading") }}</div>

    <div v-else-if="!detail" class="card-panel">
      <p class="muted">未找到 Skill 或无权查看。</p>
    </div>

    <div v-else class="stack">
      <div class="card-panel head">
        <div class="title-row">
          <div class="title">{{ detail.name }}</div>
          <el-tag effect="plain" type="info">v{{ detail.version }}</el-tag>
          <el-tag v-if="detail.category" effect="plain" type="info">{{ detail.category }}</el-tag>
        </div>
        <div v-if="detail.status === 'published'" class="actions">
          <el-button class="neutral" plain @click="onDownloadZip">{{ text("dlZip") }}</el-button>
          <el-button type="success" :loading="installing" @click="onInstallOpenClaw">{{ text("installOc") }}</el-button>
        </div>
      </div>

      <div class="card-panel">
        <div class="section-title">{{ text("desc") }}</div>
        <p class="body">{{ detail.description || "（无描述）" }}</p>
      </div>

      <div class="card-panel">
        <div class="section-title">{{ text("meta") }}</div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="作者">{{ detail.author_id ? `…${detail.author_id.slice(-10)}` : "—" }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(detail.status) }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="card-panel">
        <div class="section-title">{{ text("scanSum") }}</div>
        <div class="scan-row">
          <div v-for="row in layers" :key="row.type" class="scan-item">
            <div class="scan-name">{{ layerTitle(row.type) }}</div>
            <div class="scan-ico">
              <el-icon v-if="scanIcon(row.scan, detail.status) === 'loading'" class="spin"><Loading /></el-icon>
              <el-icon v-else-if="scanIcon(row.scan, detail.status) === 'ok'" class="ok"><CircleCheck /></el-icon>
              <el-icon v-else-if="scanIcon(row.scan, detail.status) === 'bad'" class="bad"><CircleClose /></el-icon>
              <el-icon v-else class="warn"><WarningFilled /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topbar {
  display: flex;
  justify-content: flex-start;
}

.neutral {
  border-color: var(--app-border);
  color: var(--app-text);
}

.stack {
  display: grid;
  gap: 12px;
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.title {
  font-size: 20px;
  font-weight: 700;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
}

.body {
  margin: 0;
  line-height: 1.7;
  color: var(--app-text);
}

.scan-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 900px) {
  .scan-row {
    grid-template-columns: 1fr;
  }
}

.scan-item {
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fafafa;
}

.scan-name {
  font-weight: 600;
}

.scan-ico {
  font-size: 22px;
}

.ok {
  color: #22c55e;
}

.bad {
  color: #e74c3c;
}

.warn {
  color: #6b7280;
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
</style>

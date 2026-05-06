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

function scanTone(t: string) {
  if (t === "semgrep") return "tone-semgrep";
  if (t === "clamav") return "tone-clamav";
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
    scanSum: "扫描结果",
    dlZip: "下载",
    installOc: "安装到 OpenClaw",
  };
  return map[key] ?? key;
}

onMounted(() => void load());
</script>

<template>
  <div class="detail-page">
    <div v-if="loading" class="muted">{{ text("loading") }}</div>

    <div v-else-if="!detail" class="empty-card card-panel">
      <p class="muted">未找到 Skill 或无权查看。</p>
      <el-button class="mt" type="primary" @click="router.push({ name: 'explore' })">{{ text("back") }}</el-button>
    </div>

    <div v-else class="stack">
      <el-breadcrumb separator="/" class="crumb">
        <el-breadcrumb-item :to="{ name: 'explore' }">应用市场</el-breadcrumb-item>
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

        <p class="body">{{ detail.description || "（无描述）" }}</p>

        <div class="meta-line muted">
          <span>作者：{{ detail.author_id ? `…${detail.author_id.slice(-10)}` : "—" }}</span>
          <span class="dot">·</span>
          <span>提交时间：{{ formatTime(detail.created_at) }}</span>
        </div>

        <div v-if="detail.status === 'published'" class="actions">
          <el-button type="primary" size="large" class="act-pri" @click="onDownloadZip">{{ text("dlZip") }}</el-button>
          <el-button size="large" class="act-outline" plain :loading="installing" @click="onInstallOpenClaw">{{
            text("installOc")
          }}</el-button>
        </div>
      </section>

      <section class="scan-section">
        <h2 class="section-title">{{ text("scanSum") }}</h2>
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
                <div class="scan-name">{{ layerTitle(row.type) }}</div>
                <div class="scan-badge">
                  <template v-if="scanIcon(row.scan, detail.status) === 'loading'">
                    <el-tag type="info" effect="plain" size="small">待扫描</el-tag>
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

.act-pri {
  min-width: 120px;
  font-weight: 600;
  border-radius: var(--radius-control);
}

.act-outline {
  border-radius: var(--radius-control);
  font-weight: 600;
  border-color: var(--app-primary) !important;
  color: var(--app-primary) !important;
  background: var(--app-surface) !important;
}

.act-outline:hover {
  background: rgba(26, 26, 46, 0.06) !important;
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
  background: rgba(26, 26, 46, 0.06);
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
</style>

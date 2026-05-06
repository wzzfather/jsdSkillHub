<script setup lang="ts">
import { onUnmounted, reactive, ref } from "vue";
import type { UploadRequestOptions } from "element-plus";
import { ElMessage } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import type { AxiosError } from "axios";
import { fetchSkillDetail, uploadSkill } from "@/api/skills";
import type { SkillDetail } from "@/api/types";

const CATEGORY_OPTIONS = [
  { label: "productivity", value: "productivity" },
  { label: "security", value: "security" },
  { label: "support", value: "support" },
  { label: "knowledge", value: "knowledge" },
  { label: "其他", value: "other" },
] as const;

const form = reactive({
  name: "",
  description: "",
  version: "1.0.0",
  category: "" as string,
});

const step = ref(0);
const uploading = ref(false);
const pollSkill = ref<SkillDetail | null>(null);
const queueNotified = ref(false);

const router = useRouter();
let timer: ReturnType<typeof setInterval> | undefined;

function stopPoll() {
  if (timer) clearInterval(timer);
  timer = undefined;
}

function layerTitle(t: string) {
  if (t === "semgrep") return "Semgrep 静态扫描";
  if (t === "clamav") return "ClamAV 恶意文件扫描";
  return "LLM 语义分析";
}

function scanState(skill: SkillDetail | null | undefined, type: "semgrep" | "clamav" | "llm") {
  if (!skill) return "idle" as const;
  const scan = skill.scans.find((s) => s.scan_type === type);
  if (scan) return scan.passed ? ("pass" as const) : ("fail" as const);
  if (skill.status === "scanning") return "loading" as const;
  return "idle" as const;
}

async function pollOnce(id: string) {
  const { data } = await fetchSkillDetail(id);
  pollSkill.value = data;
  if (data.status !== "scanning") {
    stopPoll();
    if (data.status === "pending_review" && !queueNotified.value) {
      queueNotified.value = true;
      ElMessage.success("已进入审批队列");
    }
  }
}

async function handleUpload(opt: UploadRequestOptions) {
  uploading.value = true;
  pollSkill.value = null;
  queueNotified.value = false;
  stopPoll();
  try {
    const fd = new FormData();
    fd.append("file", opt.file as File);
    fd.append("name", form.name.trim());
    fd.append("version", form.version.trim());
    if (form.description.trim()) fd.append("description", form.description.trim());
    const cat = (form.category || "").trim();
    if (cat) fd.append("category", cat);

    const { data } = await uploadSkill(fd);
    ElMessage.success("上传成功，扫描进行中…");
    timer = window.setInterval(() => void pollOnce(data.id), 2000);
    await pollOnce(data.id);
    step.value = 1;
  } catch (e: unknown) {
    const err = e as AxiosError<{ detail?: unknown }>;
    if (err.response?.status === 401) {
      ElMessage.error("请先登录后再上传");
      await router.push({ name: "login", query: { redirect: "/submit" } });
      return;
    }
    ElMessage.error("上传失败，请检查 zip 与网络");
  } finally {
    uploading.value = false;
  }
}

function nextStep() {
  if (!form.name.trim()) {
    ElMessage.warning("请填写名称");
    return;
  }
  step.value = 1;
}

function prevStep() {
  step.value = 0;
}

onUnmounted(() => stopPoll());
</script>

<template>
  <div class="submit-page">
    <header class="page-head">
      <h2 class="page-heading">提交应用</h2>
      <p class="muted page-lead">
        填写元数据后在第二步上传 ZIP；系统将执行 Semgrep、ClamAV、LLM 三层扫描。
      </p>
      <el-steps class="steps" finish-status="success" :active="step" align-center>
        <el-step title="基础信息" description="名称 / 版本 / 分类 / 简介" />
        <el-step title="上传与扫描" description="拖拽 zip 并观测扫描进度" />
      </el-steps>
    </header>

    <div v-if="step === 0" class="form-card card-panel">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="名称（必填）">
              <el-input v-model="form.name" placeholder="例如：工单分类助手" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="版本">
              <el-input v-model="form.version" placeholder="1.0.0" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="4" placeholder="能力说明、数据来源、注意事项" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="分类">
              <el-select v-model="form.category" clearable placeholder="选择分类">
                <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-button type="primary" class="cta" size="large" @click="nextStep">下一步</el-button>
      </el-form>
    </div>

    <div v-else class="form-card card-panel">
      <div class="step-toolbar">
        <el-button plain class="neutral" @click="prevStep">上一步</el-button>
      </div>

      <el-upload
        drag
        class="uploader"
        :disabled="uploading || !form.name.trim()"
        :http-request="handleUpload"
        accept=".zip"
        :show-file-list="false"
      >
        <el-icon class="el-icon--upload upload-ico"><UploadFilled /></el-icon>
        <div class="upload-title">拖拽文件到此处或点击上传</div>
        <template #tip>
          <div class="el-upload__tip muted">仅支持 .zip；名称需在第一步填写完整。</div>
        </template>
      </el-upload>

      <div v-if="pollSkill" class="status">
        <div class="status-row">
          <span class="muted">当前状态：</span>
          <el-tag effect="light" type="info">{{ pollSkill.status }}</el-tag>
        </div>

        <div class="scan-grid">
          <div v-for="t in ['semgrep', 'clamav', 'llm'] as const" :key="t" class="scan-card" :class="`accent-${t}`">
            <div class="scan-title">{{ layerTitle(t) }}</div>
            <div class="scan-state">
              <template v-if="scanState(pollSkill, t) === 'loading'">
                <el-tag effect="plain" type="info">进行中</el-tag>
              </template>
              <template v-else-if="scanState(pollSkill, t) === 'pass'">
                <el-tag effect="dark" type="success">已完成 · 通过</el-tag>
              </template>
              <template v-else-if="scanState(pollSkill, t) === 'fail'">
                <el-tag effect="dark" type="danger">已完成 · 不通过</el-tag>
              </template>
              <template v-else>
                <el-tag effect="plain">等待</el-tag>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.submit-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-head {
  margin-bottom: 4px;
}

.page-heading {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 800;
  color: var(--app-text);
}

.page-lead {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.6;
}

.steps {
  margin-top: 4px;
  padding: 8px 0 4px;
}

.steps :deep(.el-step__title) {
  font-weight: 600;
}

.form-card {
  padding: 24px;
}

.step-toolbar {
  margin-bottom: 14px;
}

.neutral {
  border-color: var(--app-border-strong);
  color: var(--app-text);
}

.cta {
  margin-top: 8px;
}

.uploader {
  width: 100%;
}

.uploader :deep(.el-upload-dragger) {
  border: 2px dashed var(--app-border-strong);
  border-radius: var(--radius-card);
  padding: 40px 24px;
  background: var(--app-surface);
}

.uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--app-primary-deep);
  background: var(--app-bg);
}

.upload-ico {
  font-size: 48px;
  color: var(--app-muted);
}

.upload-title {
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
}

.status {
  margin-top: 22px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scan-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 900px) {
  .scan-grid {
    grid-template-columns: 1fr;
  }
}

.scan-card {
  border: 1px solid var(--app-border);
  border-radius: var(--radius-control);
  padding: 16px;
  background: var(--app-bg);
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

.scan-title {
  font-weight: 700;
}

.scan-state {
  margin-top: 10px;
}
</style>

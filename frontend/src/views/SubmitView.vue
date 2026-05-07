<script setup lang="ts">
import { computed, onUnmounted, reactive, ref } from "vue";
import type { UploadRequestOptions } from "element-plus";
import { ElMessage } from "element-plus";
import { CircleCheck, UploadFilled } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import type { AxiosError } from "axios";
import { fetchSkillDetail, uploadSkill } from "@/api/skills";
import type { SkillDetail } from "@/api/types";
import { useLocale } from "@/locales";

const { t } = useLocale();

const categoryOptions = computed(() => [
  { label: "productivity", value: "productivity" },
  { label: "security", value: "security" },
  { label: "support", value: "support" },
  { label: "knowledge", value: "knowledge" },
  { label: t("submit.cat.other"), value: "other" },
]);

const form = reactive({
  name: "",
  description: "",
  version: "1.0.0",
  category: "" as string,
});

const step = ref(0);
const uploading = ref(false);
const pollSkill = ref<SkillDetail | null>(null);

const router = useRouter();
let timer: ReturnType<typeof setInterval> | undefined;

const showReviewQueueCard = computed(() => pollSkill.value?.status === "pending_review");

function stopPoll() {
  if (timer) clearInterval(timer);
  timer = undefined;
}

function scanLayerTitle(type: string) {
  if (type === "semgrep") return t("submit.layerSemgrep");
  if (type === "clamav") return t("submit.layerClamav");
  return t("submit.layerLlm");
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
  }
}

async function handleUpload(opt: UploadRequestOptions) {
  uploading.value = true;
  pollSkill.value = null;
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
    ElMessage.success(t("submit.msgUploaded"));
    timer = window.setInterval(() => void pollOnce(data.id), 2000);
    await pollOnce(data.id);
    step.value = 1;
  } catch (e: unknown) {
    const err = e as AxiosError<{ detail?: unknown }>;
    if (err.response?.status === 401) {
      ElMessage.error(t("submit.errAuth"));
      await router.push({ name: "login", query: { redirect: "/submit" } });
      return;
    }
    ElMessage.error(t("submit.errUpload"));
  } finally {
    uploading.value = false;
  }
}

function gotoMyApps() {
  router.push({ name: "my-apps" });
}

function resetUploadFlow() {
  stopPoll();
  pollSkill.value = null;
  form.name = "";
  form.description = "";
  form.version = "1.0.0";
  form.category = "";
  step.value = 0;
}

function nextStep() {
  if (!form.name.trim()) {
    ElMessage.warning(t("submit.warnName"));
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
      <h2 class="page-heading">{{ t("submit.title") }}</h2>
      <p class="muted page-lead">{{ t("submit.lead") }}</p>
      <el-steps class="steps" finish-status="success" :active="step" align-center>
        <el-step :title="t('submit.step1Title')" :description="t('submit.step1Desc')" />
        <el-step :title="t('submit.step2Title')" :description="t('submit.step2Desc')" />
      </el-steps>
    </header>

    <div v-if="step === 0" class="form-card card-panel">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item :label="t('submit.nameLabel')">
              <el-input v-model="form.name" :placeholder="t('submit.namePh')" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item :label="t('submit.versionLabel')">
              <el-input v-model="form.version" placeholder="1.0.0" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item :label="t('submit.descLabel')">
              <el-input v-model="form.description" type="textarea" :rows="4" :placeholder="t('submit.descPh')" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item :label="t('submit.categoryLabel')">
              <el-select v-model="form.category" clearable :placeholder="t('submit.categoryPh')">
                <el-option v-for="c in categoryOptions" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-button type="primary" class="cta" size="large" @click="nextStep">{{ t("submit.next") }}</el-button>
      </el-form>
    </div>

    <div v-else class="form-card card-panel">
      <div class="step-toolbar">
        <el-button plain class="neutral" @click="prevStep">{{ t("submit.prev") }}</el-button>
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
        <div class="upload-title">{{ t("submit.uploadTitle") }}</div>
        <template #tip>
          <div class="el-upload__tip muted">{{ t("submit.uploadTip") }}</div>
        </template>
      </el-upload>

      <div v-if="pollSkill" class="status">
        <div class="status-row">
          <span class="muted">{{ t("submit.statusPrefix") }}</span>
          <el-tag effect="light" type="info">{{ pollSkill.status }}</el-tag>
        </div>

        <div class="scan-grid">
          <div v-for="scanKind in ['semgrep', 'clamav', 'llm'] as const" :key="scanKind" class="scan-card" :class="`accent-${scanKind}`">
            <div class="scan-title">{{ scanLayerTitle(scanKind) }}</div>
            <div class="scan-state">
              <template v-if="scanState(pollSkill, scanKind) === 'loading'">
                <el-tag effect="plain" type="info">{{ t("submit.scanRunning") }}</el-tag>
              </template>
              <template v-else-if="scanState(pollSkill, scanKind) === 'pass'">
                <el-tag effect="dark" type="success">{{ t("submit.scanPass") }}</el-tag>
              </template>
              <template v-else-if="scanState(pollSkill, scanKind) === 'fail'">
                <el-tag effect="dark" type="danger">{{ t("submit.scanFail") }}</el-tag>
              </template>
              <template v-else>
                <el-tag effect="plain">{{ t("submit.scanWait") }}</el-tag>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showReviewQueueCard" class="queue-success-card" role="status">
        <div class="queue-success-icon" aria-hidden="true">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="queue-success-body">
          <div class="queue-success-title">{{ t("submit.queueTitle") }}</div>
          <p class="queue-success-desc muted">{{ t("submit.queueDesc") }}</p>
          <div class="queue-success-actions">
            <el-button type="primary" class="act-pri" @click="gotoMyApps">{{ t("submit.myApps") }}</el-button>
            <el-button plain class="neutral" @click="resetUploadFlow">{{ t("submit.continue") }}</el-button>
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

.queue-success-card {
  margin-top: 22px;
  display: flex;
  gap: 18px;
  align-items: flex-start;
  padding: 20px 22px;
  border-radius: var(--radius-card);
  border: 1px solid var(--app-border);
  background: var(--app-surface);
  box-shadow: var(--shadow-card);
}

.queue-success-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.12);
  color: var(--app-success);
  font-size: 28px;
}

.queue-success-body {
  min-width: 0;
  flex: 1;
}

.queue-success-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

.queue-success-desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.5;
}

.queue-success-actions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.act-pri {
  font-weight: 600;
  border-radius: var(--radius-control);
}
</style>

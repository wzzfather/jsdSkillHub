<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchSkills } from "@/api/skills";
import type { WorkflowOverview } from "@/api/types";
import { useAuthStore } from "@/stores/auth";
import { useLocale } from "@/locales";

const router = useRouter();
const auth = useAuthStore();
const { t } = useLocale();

const loading = ref(false);
const overview = ref<WorkflowOverview>({
  total: 0,
  scanning: 0,
  pending_review: 0,
  published: 0,
  rejected: 0,
});

async function load() {
  loading.value = true;
  try {
    const [scanning, pending_review, published, rejected] = await Promise.all([
      fetchSkills({ status: "scanning", page: 1, page_size: 1 }),
      fetchSkills({ status: "pending_review", page: 1, page_size: 1 }),
      fetchSkills({ status: "published", page: 1, page_size: 1 }),
      fetchSkills({ status: "rejected", page: 1, page_size: 1 }),
    ]);
    overview.value = {
      total:
        scanning.data.total +
        pending_review.data.total +
        published.data.total +
        rejected.data.total,
      scanning: scanning.data.total,
      pending_review: pending_review.data.total,
      published: published.data.total,
      rejected: rejected.data.total,
    };
  } catch {
    ElMessage.error(t("dashboard.errLoad"));
  } finally {
    loading.value = false;
  }
}

async function goReview() {
  await auth.ensureAdmin();
  if (!auth.isAdmin) {
    ElMessage.warning(t("dashboard.needAdmin"));
    return;
  }
  router.push({ name: "review" });
}

onMounted(() => void load());
</script>

<template>
  <div class="dash-page">
    <header class="page-head card-panel">
      <h2 class="page-heading">{{ t("dashboard.title") }}</h2>
      <p class="muted page-lead">{{ t("dashboard.sub") }}</p>
    </header>

    <el-row :gutter="16" class="kpi-row" v-loading="loading">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="kpi-card">
          <div class="icon-wrap tone-total" aria-hidden="true">
            <svg class="dash-ico" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path
                fill="currentColor"
                d="M4 17h16v3H4v-3zm2-13h12v11H6V4zm2 9h8V9H8v4z"
                opacity=".95"
              />
            </svg>
          </div>
          <div class="kpi-text">
            <div class="kpi-num">{{ overview.total }}</div>
            <div class="kpi-label muted">{{ t("dashboard.kpiTotal") }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="kpi-card">
          <div class="icon-wrap tone-scan" aria-hidden="true">
            <svg class="dash-ico" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path
                fill="currentColor"
                d="M7 18h10v3H7v-3zM15 11h6v11h-2v-9h-4v2h-8V4h2v15h11v2H13V9zM7 14V4h2v10H7zm4-10h2v5h-2V4z"
              />
            </svg>
          </div>
          <div class="kpi-text">
            <div class="kpi-num">{{ overview.scanning }}</div>
            <div class="kpi-label muted">{{ t("dashboard.kpiScan") }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="kpi-card">
          <div class="icon-wrap tone-pending" aria-hidden="true">
            <svg class="dash-ico" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path
                fill="currentColor"
                d="M12 20a8 8 0 110-16 8 8 0 010 16zm1-13h-2v6l5 3 .9-1.5-3.9-2.3V7z"
              />
            </svg>
          </div>
          <div class="kpi-text">
            <div class="kpi-num">{{ overview.pending_review }}</div>
            <div class="kpi-label muted">{{ t("dashboard.kpiPending") }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="kpi-card">
          <div class="icon-wrap tone-pub" aria-hidden="true">
            <svg class="dash-ico" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M10 15.2l-3.5-3.5-1.4 1.4L10 18l7.1-7.1-1.4-1.4L10 15.2z" />
            </svg>
          </div>
          <div class="kpi-text">
            <div class="kpi-num">{{ overview.published }}</div>
            <div class="kpi-label muted">{{ t("dashboard.kpiPub") }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="actions card-panel">
      <el-button type="primary" plain @click="router.push({ name: 'explore' })">{{ t("dashboard.goExplore") }}</el-button>
      <el-button type="success" plain @click="router.push({ name: 'submit' })">{{ t("dashboard.goSubmit") }}</el-button>
      <el-button type="danger" plain @click="goReview">{{ t("dashboard.goReview") }}</el-button>
    </div>
  </div>
</template>

<style scoped>
.dash-page {
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
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

.kpi-row {
  margin-top: 2px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-card);
  padding: 24px;
  box-shadow: var(--shadow-card);
  height: 100%;
  box-sizing: border-box;
}

.kpi-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.dash-ico {
  width: 26px;
  height: 26px;
  display: block;
}

.tone-total {
  background: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%);
}

.tone-scan {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
}

.tone-pending {
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
}

.tone-pub {
  background: linear-gradient(135deg, #22c55e 0%, #14b8a6 100%);
}

.kpi-text {
  min-width: 0;
}

.kpi-num {
  font-size: 28px;
  font-weight: 800;
  color: var(--app-text);
  line-height: 1.05;
}

.kpi-label {
  margin-top: 6px;
  font-size: 13px;
  font-weight: 600;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 18px 24px;
}
</style>

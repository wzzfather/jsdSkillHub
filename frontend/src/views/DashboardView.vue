<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchSkills } from "@/api/skills";
import type { WorkflowOverview } from "@/api/types";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

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
    ElMessage.error("加载看板数据失败");
  } finally {
    loading.value = false;
  }
}

function text(key: string) {
  const map: Record<string, string> = {
    headline: "看板总览",
    sub: "KPI 来自多次 GET /api/skills（按 status 取 total 字段后汇总）。",
    total: "总 Skill 数",
    scan: "扫描中",
    pending: "待审批",
    pub: "已上架",
    rej: "已驳回",
    goExplore: "浏览市场",
    goSubmit: "提交应用",
    goReview: "审批工作台",
  };
  return map[key] ?? key;
}

async function goReview() {
  await auth.ensureAdmin();
  if (!auth.isAdmin) {
    ElMessage.warning("需要管理员权限");
    return;
  }
  router.push({ name: "review" });
}

onMounted(() => void load());
</script>

<template>
  <div class="dash-wrap">
    <div class="card-panel">
      <h2 class="page-title">{{ text("headline") }}</h2>
      <p class="muted">{{ text("sub") }}</p>

      <el-row :gutter="12" class="kpi-row" v-loading="loading">
        <el-col :xs="12" :md="8" :lg="4">
          <div class="kpi">
            <b>{{ overview.total }}</b><span>{{ text("total") }}</span>
          </div>
        </el-col>
        <el-col :xs="12" :md="8" :lg="4">
          <div class="kpi">
            <b>{{ overview.scanning }}</b><span>{{ text("scan") }}</span>
          </div>
        </el-col>
        <el-col :xs="12" :md="8" :lg="4">
          <div class="kpi">
            <b>{{ overview.pending_review }}</b><span>{{ text("pending") }}</span>
          </div>
        </el-col>
        <el-col :xs="12" :md="8" :lg="4">
          <div class="kpi">
            <b>{{ overview.published }}</b><span>{{ text("pub") }}</span>
          </div>
        </el-col>
        <el-col :xs="12" :md="8" :lg="4">
          <div class="kpi">
            <b>{{ overview.rejected }}</b><span>{{ text("rej") }}</span>
          </div>
        </el-col>
      </el-row>

      <div class="actions">
        <el-button type="primary" plain @click="router.push({ name: 'explore' })">{{ text("goExplore") }}</el-button>
        <el-button type="success" plain @click="router.push({ name: 'submit' })">{{ text("goSubmit") }}</el-button>
        <el-button type="danger" plain @click="goReview">{{ text("goReview") }}</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-row {
  margin-top: 12px;
}

.kpi {
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 16px;
  display: grid;
  gap: 6px;
  background: #fafafa;
}

.kpi b {
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text);
}

.kpi span {
  color: var(--app-muted);
  font-size: 12px;
}

.actions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>

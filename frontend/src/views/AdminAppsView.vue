<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchAdminSkills, offlineSkill, republishSkill } from "@/api/skills";
import type { SkillAdmin } from "@/api/types";

const router = useRouter();

const loading = ref(false);
const forbidden = ref(false);
const rows = ref<SkillAdmin[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const statusFilter = ref<"" | "scanning" | "pending_review" | "published" | "offline" | "rejected">("");

const offlineVisible = ref(false);
const offlineReason = ref("");
const offlineTarget = ref<SkillAdmin | null>(null);

const statusTabs: { key: typeof statusFilter.value; label: string }[] = [
  { key: "", label: "全部" },
  { key: "scanning", label: "scanning" },
  { key: "pending_review", label: "pending_review" },
  { key: "published", label: "published" },
  { key: "offline", label: "offline" },
  { key: "rejected", label: "rejected" },
];

function formatTime(iso?: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function authorCell(row: SkillAdmin) {
  if (row.author_username) return row.author_username;
  const id = row.author_id;
  if (!id) return "—";
  return id.length <= 12 ? id : `…${id.slice(-10)}`;
}

function categoryCell(row: SkillAdmin) {
  return row.category && row.category.trim() ? row.category : "—";
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    scanning: "扫描中",
    pending_review: "待审核",
    published: "已上架",
    offline: "已下架",
    rejected: "已驳回",
  };
  return map[s] ?? s;
}

function statusTagType(s: string): "success" | "warning" | "info" | "danger" {
  if (s === "scanning") return "warning";
  if (s === "pending_review") return "info";
  if (s === "published") return "success";
  if (s === "offline" || s === "rejected") return "danger";
  return "info";
}

async function reload() {
  loading.value = true;
  forbidden.value = false;
  try {
    const { data } = await fetchAdminSkills({
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: pageSize,
    });
    rows.value = data.items;
    total.value = data.total;
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } };
    if (err.response?.status === 403) forbidden.value = true;
    ElMessage.error("加载应用列表失败");
  } finally {
    loading.value = false;
  }
}

function openOffline(row: SkillAdmin) {
  offlineTarget.value = row;
  offlineReason.value = "";
  offlineVisible.value = true;
}

async function confirmOffline() {
  const row = offlineTarget.value;
  if (!row) return;
  const reason = offlineReason.value.trim();
  if (!reason) {
    ElMessage.warning("请填写下架原因");
    return;
  }
  try {
    const { data } = await offlineSkill(row.id, reason);
    ElMessage.success(data.message);
    offlineVisible.value = false;
    offlineTarget.value = null;
    await reload();
  } catch {
    ElMessage.error("下架失败");
  }
}

async function onRepublish(row: SkillAdmin) {
  try {
    const { data } = await republishSkill(row.id);
    ElMessage.success(data.message);
    await reload();
  } catch {
    ElMessage.error("重新上架失败");
  }
}

function goDetail(row: SkillAdmin) {
  router.push({ name: "skill-detail", params: { id: row.id } });
}

function goReview() {
  router.push({ name: "review" });
}

watch(statusFilter, () => {
  page.value = 1;
});

watch(
  [statusFilter, page],
  () => {
    void reload();
  },
  { immediate: true },
);
</script>

<template>
  <div class="admin-apps">
    <header class="filter-hero card-panel">
      <h1 class="page-heading">应用管理</h1>
      <p class="muted page-lead">查看并管理各状态 Skill，支持下架与重新上架。</p>

      <div class="pill-row">
        <button
          v-for="t in statusTabs"
          :key="t.key || 'all'"
          type="button"
          class="pill"
          :class="{ active: statusFilter === t.key }"
          @click="statusFilter = t.key"
        >
          {{ t.label }}
        </button>
      </div>
    </header>

    <div v-if="forbidden" class="muted">无权访问此页面。</div>
    <div v-else-if="loading" class="muted loading">加载中…</div>
    <el-card v-else class="table-card" shadow="never">
      <el-table :data="rows" stripe class="apps-table" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column label="作者" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ authorCell(row) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分类" width="130" show-overflow-tooltip>
          <template #default="{ row }">
            {{ categoryCell(row) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'published'">
              <el-button type="danger" size="small" plain @click="openOffline(row)">下架</el-button>
            </template>
            <template v-else-if="row.status === 'offline'">
              <el-button type="success" size="small" plain @click="onRepublish(row)">重新上架</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-button size="small" plain @click="goDetail(row)">查看</el-button>
            </template>
            <template v-else-if="row.status === 'pending_review'">
              <el-button size="small" plain @click="goReview()">查看</el-button>
            </template>
            <template v-else>
              <el-button size="small" plain @click="goDetail(row)">查看</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > 0" class="pager">
        <el-pagination
          v-model:current-page="page"
          background
          layout="prev, pager, next, total"
          :page-size="pageSize"
          :total="total"
        />
      </div>
    </el-card>

    <el-dialog v-model="offlineVisible" title="下架应用" width="520px" destroy-on-close align-center append-to-body>
      <p class="muted dialog-hint">请填写下架原因，提交后将立即变为已下架。</p>
      <el-input v-model="offlineReason" type="textarea" :rows="4" placeholder="下架原因…" maxlength="2000" show-word-limit />
      <template #footer>
        <el-button @click="offlineVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmOffline">确认下架</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-apps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-heading {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 800;
}

.page-lead {
  margin: 0 0 14px;
  font-size: 14px;
  line-height: 1.6;
}

.filter-hero {
  padding: 24px;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.pill {
  appearance: none;
  border-radius: 999px;
  border: 1px solid var(--app-border-strong);
  background: var(--app-surface);
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  font-family: inherit;
}

.pill.active {
  background: var(--app-primary);
  border-color: var(--app-primary);
  color: #fff;
}

.pill:hover:not(.active) {
  border-color: var(--app-primary-deep);
  color: var(--app-primary);
}

.loading {
  padding: 12px 4px;
}

.table-card :deep(.el-card__body) {
  padding: 0 0 8px;
}

.apps-table :deep(.cell) {
  padding-top: 14px;
  padding-bottom: 14px;
}

.pager {
  display: flex;
  justify-content: center;
  padding: 10px 0 14px;
}

.dialog-hint {
  margin: 0 0 10px;
  font-size: 13px;
}
</style>

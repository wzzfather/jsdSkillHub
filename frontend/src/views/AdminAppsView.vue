<script setup lang="ts">
import { ref, watch, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { fetchAdminSkills, fetchSkillCategories, offlineSkill, republishSkill } from "@/api/skills";
import { approveSkill, rejectSkill } from "@/api/reviews";
import type { SkillAdmin } from "@/api/types";
import { useLocale } from "@/locales";

const router = useRouter();
const { t } = useLocale();

const loading = ref(false);
const forbidden = ref(false);
const rows = ref<SkillAdmin[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const statusFilter = ref<"" | "scanning" | "pending_review" | "published" | "offline" | "rejected">("");

// 新增筛选
const searchQuery = ref("");
const debouncedSearch = ref("");
const categoryFilter = ref("");
const authorFilter = ref("");
const debouncedAuthor = ref("");

// 动态分类
const DEFAULT_CATEGORIES = ["productivity", "security", "support", "knowledge"];
const dynamicCategories = ref<string[]>([]);

// 下架对话框
const offlineVisible = ref(false);
const offlineReason = ref("");
const offlineTarget = ref<SkillAdmin | null>(null);

// 驳回对话框
const rejectVisible = ref(false);
const rejectReason = ref("");
const rejectTarget = ref<SkillAdmin | null>(null);

// 快捷审批 loading
const approvingId = ref<string | null>(null);
const rejectingId = ref<string | null>(null);

const statusTabs = computed(() => [
  { key: "" as const, label: t("admin.tabAll") },
  { key: "scanning" as const, label: t("skillStatus.scanning") },
  { key: "pending_review" as const, label: t("skillStatus.pending_review_admin") },
  { key: "published" as const, label: t("skillStatus.published") },
  { key: "offline" as const, label: t("skillStatus.offline") },
  { key: "rejected" as const, label: t("skillStatus.rejected") },
]);

async function loadCategories() {
  try {
    const { data } = await fetchSkillCategories();
    const list = data.items ?? [];
    dynamicCategories.value = list.length > 0 ? list : DEFAULT_CATEGORIES;
  } catch {
    dynamicCategories.value = DEFAULT_CATEGORIES;
  }
}

onMounted(() => {
  void loadCategories();
});

function formatTime(iso?: string | null) {
  if (!iso) return t("common.emDash");
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function authorCell(row: SkillAdmin) {
  if (row.author_username) return row.author_username;
  const id = row.author_id;
  if (!id) return t("common.emDash");
  return id.length <= 12 ? id : `…${id.slice(-10)}`;
}

function categoryCell(row: SkillAdmin) {
  return row.category && row.category.trim() ? row.category : t("common.emDash");
}

function statusLabel(s: string) {
  const keys: Record<string, string> = {
    scanning: "skillStatus.scanning",
    pending_review: "skillStatus.pending_review_admin",
    published: "skillStatus.published",
    offline: "skillStatus.offline",
    rejected: "skillStatus.rejected",
  };
  const k = keys[s];
  return k ? t(k) : s;
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
      search: debouncedSearch.value || undefined,
      category: categoryFilter.value || undefined,
      author: debouncedAuthor.value || undefined,
    });
    rows.value = data.items;
    total.value = data.total;
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } };
    if (err.response?.status === 403) forbidden.value = true;
    ElMessage.error(t("admin.errLoad"));
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
    ElMessage.warning(t("admin.warnOfflineReason"));
    return;
  }
  try {
    const { data } = await offlineSkill(row.id, reason);
    ElMessage.success(data.message);
    offlineVisible.value = false;
    offlineTarget.value = null;
    await reload();
  } catch {
    ElMessage.error(t("admin.errOffline"));
  }
}

async function onRepublish(row: SkillAdmin) {
  try {
    await republishSkill(row.id);
    ElMessage.success(t("admin.okRepublish"));
    await reload();
  } catch {
    ElMessage.error(t("admin.errRepublish"));
  }
}

function openReject(row: SkillAdmin) {
  rejectTarget.value = row;
  rejectReason.value = "";
  rejectVisible.value = true;
}

async function confirmReject() {
  const row = rejectTarget.value;
  if (!row) return;
  const reason = rejectReason.value.trim();
  if (!reason) {
    ElMessage.warning(t("admin.warnRejectReason"));
    return;
  }
  rejectingId.value = row.id;
  try {
    const { data } = await rejectSkill(row.id, reason);
    ElMessage.success(data.message);
    rejectVisible.value = false;
    rejectTarget.value = null;
    await reload();
  } catch {
    ElMessage.error(t("admin.errReject"));
  } finally {
    rejectingId.value = null;
  }
}

async function onQuickApprove(row: SkillAdmin) {
  approvingId.value = row.id;
  try {
    const { data } = await approveSkill(row.id);
    ElMessage.success(data.message);
    await reload();
  } catch {
    ElMessage.error(t("admin.errApprove"));
  } finally {
    approvingId.value = null;
  }
}

function goDetail(row: SkillAdmin) {
  router.push({ name: "skill-detail", params: { id: row.id } });
}

// goReview 保留：未来可能用于跳转到审批工作台

// 防抖
watch(searchQuery, (_q, _o, onCleanup) => {
  const tid = window.setTimeout(() => {
    debouncedSearch.value = searchQuery.value.trim();
  }, 300);
  onCleanup(() => clearTimeout(tid));
});

watch(authorFilter, (_q, _o, onCleanup) => {
  const tid = window.setTimeout(() => {
    debouncedAuthor.value = authorFilter.value.trim();
  }, 300);
  onCleanup(() => clearTimeout(tid));
});

// 筛选变化时重置页码
watch([statusFilter, categoryFilter, debouncedSearch, debouncedAuthor], () => {
  page.value = 1;
});

watch(
  [statusFilter, page, categoryFilter, debouncedSearch, debouncedAuthor],
  () => {
    void reload();
  },
  { immediate: true },
);
</script>

<template>
  <div class="admin-apps">
    <header class="filter-hero card-panel">
      <h1 class="page-heading">{{ t("admin.title") }}</h1>
      <p class="muted page-lead">{{ t("admin.lead") }}</p>

      <div class="pill-row">
        <button
          v-for="tab in statusTabs"
          :key="tab.key || 'all'"
          type="button"
          class="pill"
          :class="{ active: statusFilter === tab.key }"
          @click="statusFilter = tab.key as typeof statusFilter.value"
        >
          {{ tab.label }}
        </button>
      </div>
    </header>

    <!-- 搜索和筛选栏 -->
    <div class="filter-bar card-panel">
      <div class="filter-bar-inner">
        <el-input
          v-model="searchQuery"
          class="filter-search"
          clearable
          :placeholder="t('admin.searchPh')"
          size="default"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="categoryFilter" class="filter-select" clearable :placeholder="t('admin.categoryPh')">
          <el-option :label="t('admin.categoryAll')" value="" />
          <el-option v-for="cat in dynamicCategories" :key="cat" :label="cat" :value="cat" />
        </el-select>

        <el-input
          v-model="authorFilter"
          class="filter-author"
          clearable
          :placeholder="t('admin.authorPh')"
          size="default"
        />
      </div>
    </div>

    <p class="workflow-hint muted">
      <strong>{{ t("admin.workflowStrong") }}</strong>
      {{ t("admin.workflowBody") }}
    </p>

    <div v-if="forbidden" class="muted">{{ t("admin.forbidden") }}</div>
    <div v-else-if="loading" class="muted loading">{{ t("common.loading") }}</div>
    <el-card v-else class="table-card" shadow="never">
      <el-table :data="rows" stripe class="apps-table" style="width: 100%">
        <el-table-column prop="name" :label="t('admin.col.name')" min-width="160" show-overflow-tooltip />
        <el-table-column prop="version" :label="t('admin.col.version')" width="100" />
        <el-table-column :label="t('admin.col.author')" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ authorCell(row) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('admin.col.status')" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('admin.col.category')" width="130" show-overflow-tooltip>
          <template #default="{ row }">
            {{ categoryCell(row) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('admin.col.created')" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('admin.col.action')" width="260" fixed="right">
          <template #default="{ row }">
            <!-- published -->
            <template v-if="row.status === 'published'">
              <el-button type="danger" size="small" plain @click="openOffline(row)">{{ t("admin.action.offline") }}</el-button>
              <el-button size="small" plain @click="goDetail(row)">{{ t("admin.action.view") }}</el-button>
            </template>
            <!-- pending -->
            <template v-else-if="row.status === 'pending_review'">
              <el-button
                type="success"
                size="small"
                plain
                :loading="approvingId === row.id"
                @click="onQuickApprove(row)"
              >
                {{ t("admin.action.approve") }}
              </el-button>
              <el-button
                type="danger"
                size="small"
                plain
                :loading="rejectingId === row.id"
                @click="openReject(row)"
              >
                {{ t("admin.action.reject") }}
              </el-button>
              <el-button size="small" plain @click="goDetail(row)">{{ t("admin.action.view") }}</el-button>
            </template>
            <!-- offline -->
            <template v-else-if="row.status === 'offline'">
              <el-button type="success" size="small" plain @click="onRepublish(row)">{{ t("admin.action.republish") }}</el-button>
              <el-button size="small" plain @click="goDetail(row)">{{ t("admin.action.view") }}</el-button>
            </template>
            <!-- rejected / scanning / other -->
            <template v-else>
              <el-button size="small" plain @click="goDetail(row)">{{ t("admin.action.view") }}</el-button>
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

    <!-- 下架对话框 -->
    <el-dialog v-model="offlineVisible" :title="t('admin.dialog.offlineTitle')" width="520px" destroy-on-close align-center append-to-body>
      <p class="muted dialog-hint">{{ t("admin.dialog.offlineHint") }}</p>
      <el-input v-model="offlineReason" type="textarea" :rows="4" :placeholder="t('admin.dialog.offlinePlaceholder')" maxlength="2000" show-word-limit />
      <template #footer>
        <el-button @click="offlineVisible = false">{{ t("admin.dialog.cancel") }}</el-button>
        <el-button type="danger" @click="confirmOffline">{{ t("admin.dialog.offlineConfirm") }}</el-button>
      </template>
    </el-dialog>

    <!-- 驳回对话框 -->
    <el-dialog v-model="rejectVisible" :title="t('admin.dialog.rejectTitle')" width="520px" destroy-on-close align-center append-to-body>
      <p class="muted dialog-hint">{{ t("admin.dialog.rejectHint") }}</p>
      <el-input v-model="rejectReason" type="textarea" :rows="4" :placeholder="t('admin.dialog.rejectPlaceholder')" maxlength="2000" show-word-limit />
      <template #footer>
        <el-button @click="rejectVisible = false">{{ t("admin.dialog.cancel") }}</el-button>
        <el-button type="danger" @click="confirmReject">{{ t("admin.dialog.rejectConfirm") }}</el-button>
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

.workflow-hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
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

.filter-bar {
  padding: 16px 20px;
}

.filter-bar-inner {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filter-search {
  width: 240px;
  flex-shrink: 0;
}

.filter-select {
  width: 160px;
}

.filter-author {
  width: 180px;
}

.filter-search :deep(.el-input__wrapper),
.filter-author :deep(.el-input__wrapper) {
  border-radius: var(--radius-control);
}

.filter-select :deep(.el-select__wrapper) {
  border-radius: var(--radius-control);
  min-height: 32px;
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

@media (max-width: 768px) {
  .filter-search,
  .filter-select,
  .filter-author {
    width: 100%;
  }
}
</style>

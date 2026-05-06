<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchMySkills, resubmitSkill } from "@/api/skills";
import type { Skill } from "@/api/types";

const router = useRouter();
const loading = ref(false);
const items = ref<Skill[]>([]);
const resubmitingId = ref<string | null>(null);

function statusType(status: string) {
  const m: Record<string, string> = {
    scanning: "",
    pending_review: "warning",
    published: "success",
    rejected: "danger",
    offline: "info",
  };
  return (m[status] ?? "info") as "" | "success" | "warning" | "danger" | "info";
}

function statusLabel(status: string) {
  const m: Record<string, string> = {
    scanning: "扫描中",
    pending_review: "待审批",
    published: "已上架",
    rejected: "已驳回",
    offline: "已下架",
    draft: "草稿",
  };
  return m[status] ?? status;
}

const waitingStatuses = computed(() => new Set(["scanning", "pending_review"]));

async function load() {
  loading.value = true;
  try {
    const all: Skill[] = [];
    let p = 1;
    while (true) {
      const { data } = await fetchMySkills({ page: p, page_size: 100 });
      all.push(...data.items);
      if (data.items.length === 0 || all.length >= data.total) break;
      p += 1;
    }
    items.value = all;
  } catch {
    ElMessage.error("加载失败");
  } finally {
    loading.value = false;
  }
}

function goDetail(s: Skill) {
  router.push({ name: "skill-detail", params: { id: s.id } });
}

async function onResubmit(s: Skill) {
  resubmitingId.value = s.id;
  try {
    await resubmitSkill(s.id);
    ElMessage.success("已重新提交，已进入审批");
    await load();
  } catch {
    ElMessage.error("重新提交失败");
  } finally {
    resubmitingId.value = null;
  }
}

onMounted(() => void load());
</script>

<template>
  <div>
    <div class="card-panel">
      <h2 class="page-title">我的应用</h2>
      <p class="muted">你提交的 Skill（含扫描中、待审批、已上架等所有状态）。</p>
    </div>

    <div v-if="loading" class="muted" style="padding: 12px">加载中…</div>

    <el-empty v-else-if="items.length === 0" description="暂无 Skill 记录" />

    <div v-else class="card-panel" style="margin-top: 16px">
      <el-table :data="items" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <span class="link" @click="goDetail(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="category" label="分类" width="140">
          <template #default="{ row }">
            {{ row.category || "—" }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="160">
          <template #default="{ row }">
            <template v-if="waitingStatuses.has(row.status)">
              <el-tag type="warning" size="small">等待处理</el-tag>
              <span class="muted wait-hint">{{ statusLabel(row.status) }}</span>
            </template>
            <template v-else-if="row.status === 'offline'">
              <el-tag type="info" size="small">已下架</el-tag>
              <div v-if="row.offline_comment" class="offline-reason muted">
                原因：{{ row.offline_comment }}
              </div>
            </template>
            <el-tag v-else :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <template v-if="row.status === 'published'">
              <el-button text type="primary" size="small" @click="goDetail(row)">查看详情</el-button>
            </template>
            <template v-else-if="row.status === 'rejected'">
              <el-button
                text
                type="primary"
                size="small"
                :loading="resubmitingId === row.id"
                @click="onResubmit(row)"
              >
                重新提交
              </el-button>
            </template>
            <template v-else-if="!waitingStatuses.has(row.status) && row.status !== 'offline'">
              <el-button text type="primary" size="small" @click="goDetail(row)">详情</el-button>
            </template>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.page-title {
  margin: 0 0 8px;
}

.link {
  color: var(--app-text);
  cursor: pointer;
  font-weight: 500;
}

.link:hover {
  text-decoration: underline;
}

.wait-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
}

.offline-reason {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.4;
  max-width: 220px;
}
</style>

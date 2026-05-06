<script setup lang="ts">
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchSkills } from "@/api/skills";
import type { Skill } from "@/api/types";

const router = useRouter();

const loading = ref(false);
const items = ref<Skill[]>([]);
const total = ref(0);
const query = ref("");
const debouncedSearch = ref("");
const categoryFilter = ref("");
const sortBy = ref<"newest" | "popular">("newest");
const page = ref(1);
const pageSize = 12;

function skillCategoryLabel(skill: Skill) {
  return skill.category && skill.category.trim() ? skill.category : "—";
}

function authorLabel(skill: Skill) {
  const id = skill.author_id;
  if (!id) return "—";
  return id.length <= 12 ? id : `…${id.slice(-10)}`;
}

async function loadPage() {
  loading.value = true;
  try {
    const cat = typeof categoryFilter.value === "string" ? categoryFilter.value.trim().toLowerCase() : "";

    const { data } = await fetchSkills({
      status: "published",
      page: page.value,
      page_size: pageSize,
      category: cat || undefined,
      sort: sortBy.value,
      search: debouncedSearch.value || undefined,
    });
    items.value = data.items;
    total.value = data.total;
  } catch {
    ElMessage.error("加载市场列表失败");
  } finally {
    loading.value = false;
  }
}

watch(query, (_q, _o, onCleanup) => {
  const tid = window.setTimeout(() => {
    debouncedSearch.value = query.value.trim();
  }, 300);
  onCleanup(() => clearTimeout(tid));
});

watch(debouncedSearch, () => {
  page.value = 1;
});

watch([categoryFilter, sortBy], () => {
  page.value = 1;
});

watch(
  [categoryFilter, sortBy, page, debouncedSearch],
  () => {
    void loadPage();
  },
  { immediate: true },
);

function goDetail(s: Skill) {
  router.push({ name: "skill-detail", params: { id: s.id } });
}

function text(key: string) {
  const map: Record<string, string> = {
    headline: "应用市场",
    sub: "已上架 Skill 一览，可使用搜索与分类快速定位。",
    searchPh: "按名称或简介搜索…",
    empty: "暂无符合条件的 Skill",
    category: "分类",
    sort: "排序",
  };
  return map[key] ?? key;
}
</script>

<template>
  <div>
    <div class="card-panel hero">
      <h1 class="page-title">{{ text("headline") }}</h1>
      <p class="muted">{{ text("sub") }}</p>
      <el-input v-model="query" class="search" clearable :placeholder="text('searchPh')" />
      <div class="filters">
        <div class="filter-item">
          <span class="filter-label muted">{{ text("category") }}</span>
          <el-select v-model="categoryFilter" class="filter-control" placeholder="全部分类">
            <el-option label="全部" value="" />
            <el-option label="productivity" value="productivity" />
            <el-option label="security" value="security" />
            <el-option label="support" value="support" />
            <el-option label="knowledge" value="knowledge" />
            <el-option label="其他" value="other" />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label muted">{{ text("sort") }}</span>
          <el-select v-model="sortBy" class="filter-control">
            <el-option label="最新上架" value="newest" />
            <el-option label="名称排序" value="popular" />
          </el-select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="muted loading">加载中…</div>

    <el-empty v-else-if="items.length === 0" :description="text('empty')" />

    <el-row v-else :gutter="16" class="grid">
      <el-col v-for="s in items" :key="s.id" :xs="24" :sm="12" :md="8" :lg="6">
        <div
          class="skill-card card-panel"
          role="button"
          tabindex="0"
          @click="goDetail(s)"
          @keydown.enter.prevent="goDetail(s)"
        >
          <div class="name">{{ s.name }}</div>
          <div class="meta muted">v{{ s.version }}</div>
          <div class="tagline">
            <el-tag size="small" effect="plain" type="info">{{ skillCategoryLabel(s) }}</el-tag>
          </div>
          <p class="desc line-clamp-2">{{ s.description || "（无简介）" }}</p>
          <div class="foot muted">作者：{{ authorLabel(s) }}</div>
        </div>
      </el-col>
    </el-row>

    <div v-if="!loading && total > 0" class="pager">
      <el-pagination
        v-model:current-page="page"
        background
        layout="prev, pager, next, total"
        :page-size="pageSize"
        :total="total"
      />
    </div>
  </div>
</template>

<style scoped>
.hero {
  margin-bottom: 16px;
}

.search {
  margin-top: 12px;
  max-width: 520px;
}

.filters {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 200px;
}

.filter-label {
  font-size: 12px;
}

.filter-control {
  width: 220px;
  max-width: 100%;
}

.loading {
  padding: 12px 4px;
}

.grid {
  margin-top: 8px;
}

.skill-card {
  height: 100%;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.skill-card:hover {
  border-color: #a3a3a3;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
}

.skill-card:focus-visible {
  outline: 2px solid var(--app-border);
  outline-offset: 2px;
}

.name {
  font-weight: 700;
  font-size: 16px;
}

.meta {
  margin-top: 6px;
  font-size: 12px;
}

.tagline {
  margin-top: 10px;
}

.desc {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.55;
}

.foot {
  margin-top: 12px;
  font-size: 12px;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>

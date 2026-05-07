<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { fetchSkills, fetchSkillCategories } from "@/api/skills";
import type { Skill } from "@/api/types";
import { useLocale } from "@/locales";

const router = useRouter();
const { t } = useLocale();

const loading = ref(false);
const items = ref<Skill[]>([]);
const total = ref(0);
const query = ref("");
const debouncedSearch = ref("");
const categoryFilter = ref("");
const authorFilter = ref("");
const debouncedAuthor = ref("");
const sortBy = ref<"newest" | "name" | "install_count">("newest");
const page = ref(1);
const pageSize = 12;

const DEFAULT_CATEGORIES = ["productivity", "security", "support", "knowledge"];
const dynamicCategories = ref<string[]>([]);
const categoriesLoaded = ref(false);

async function loadCategories() {
  try {
    const { data } = await fetchSkillCategories();
    const list = data.items ?? [];
    if (list.length > 0) {
      dynamicCategories.value = list;
    } else {
      dynamicCategories.value = DEFAULT_CATEGORIES;
    }
    categoriesLoaded.value = true;
  } catch {
    // fallback 到默认分类
    dynamicCategories.value = DEFAULT_CATEGORIES;
    categoriesLoaded.value = true;
  }
}

onMounted(() => {
  void loadCategories();
});

function skillCategoryLabel(skill: Skill) {
  return skill.category && skill.category.trim() ? skill.category : t("common.emDash");
}

function authorLabel(skill: Skill) {
  const id = skill.author_id;
  if (!id) return t("common.emDash");
  return id.length <= 12 ? id : `…${id.slice(-10)}`;
}

function heroToneClass(cat: string | null | undefined) {
  const c = (cat ?? "").trim().toLowerCase();
  if (c === "productivity") return "tone-productivity";
  if (c === "security") return "tone-security";
  if (c === "support") return "tone-support";
  if (c === "knowledge") return "tone-knowledge";
  if (c === "other" || c === "其他") return "tone-other";
  return "tone-default";
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
      author: debouncedAuthor.value || undefined,
    });
    items.value = data.items;
    total.value = data.total;
  } catch {
    ElMessage.error(t("explore.errLoad"));
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

watch(authorFilter, (_q, _o, onCleanup) => {
  const tid = window.setTimeout(() => {
    debouncedAuthor.value = authorFilter.value.trim();
  }, 300);
  onCleanup(() => clearTimeout(tid));
});

watch(debouncedSearch, () => {
  page.value = 1;
});

watch(debouncedAuthor, () => {
  page.value = 1;
});

watch([categoryFilter, sortBy], () => {
  page.value = 1;
});

watch(
  [categoryFilter, sortBy, page, debouncedSearch, debouncedAuthor],
  () => {
    void loadPage();
  },
  { immediate: true },
);

function goDetail(s: Skill) {
  router.push({ name: "skill-detail", params: { id: s.id } });
}

function heroStat(): string {
  return t("explore.publishedStat").replace("{n}", String(total.value));
}
</script>

<template>
  <div class="explore-page">
    <header class="hero">
      <div class="hero-top">
        <div class="hero-copy">
          <h1 class="hero-title">{{ t("explore.heroTitle") }}</h1>
          <p class="hero-sub">{{ t("explore.heroSub") }}</p>
        </div>
        <el-tag v-if="!loading && total >= 0" class="hero-stat" type="info" effect="light" round>
          {{ heroStat() }}
        </el-tag>
      </div>

      <div class="search-wrap">
        <el-input v-model="query" class="search-input" clearable size="large" :placeholder="t('explore.searchPh')">
          <template #prefix>
            <el-icon class="search-ico"><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="filters">
        <div class="filter-block">
          <span class="filter-label">{{ t("explore.category") }}</span>
          <el-radio-group v-model="categoryFilter" class="cat-radio-group" size="large">
            <el-radio-button label="">{{ t("common.all") }}</el-radio-button>
            <el-radio-button v-for="cat in dynamicCategories" :key="cat" :label="cat">
              {{ cat }}
            </el-radio-button>
          </el-radio-group>
        </div>
        <div class="filter-block">
          <span class="filter-label">{{ t("explore.author") }}</span>
          <el-input
            v-model="authorFilter"
            class="author-input"
            clearable
            size="large"
            :placeholder="t('explore.authorPh')"
          />
        </div>
        <div class="filter-block sort-block">
          <span class="filter-label">{{ t("explore.sort") }}</span>
          <el-select v-model="sortBy" class="sort-select" :placeholder="t('explore.sortPh')">
            <el-option :label="t('explore.sortNewest')" value="newest" />
            <el-option :label="t('explore.sortName')" value="name" />
            <el-option :label="t('explore.sortHot')" value="install_count" />
          </el-select>
        </div>
      </div>
    </header>

    <div v-if="loading" class="muted loading">{{ t("common.loading") }}</div>

    <el-empty v-else-if="items.length === 0" :description="t('explore.empty')" />

    <el-row v-else :gutter="20" class="grid">
      <el-col v-for="s in items" :key="s.id" :xs="24" :sm="12" :md="8" :lg="6">
        <div
          class="skill-card"
          role="button"
          tabindex="0"
          @click="goDetail(s)"
          @keydown.enter.prevent="goDetail(s)"
        >
          <div class="skill-hero" :class="heroToneClass(s.category)">
            <svg class="hero-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M12 2l7 4v8l-7 4-7-4V6l7-4zm0 2.2L6.5 7.1v6.3L12 17l5.5-3.6V7.1L12 4.2z"
                opacity="0.95"
              />
            </svg>
          </div>
          <div class="skill-body">
            <div class="name">{{ s.name }}</div>
            <div class="tags-row">
              <el-tag size="small" effect="plain" type="info">v{{ s.version }}</el-tag>
              <el-tag size="small" effect="light" type="info">{{ skillCategoryLabel(s) }}</el-tag>
            </div>
            <p class="desc line-clamp-2">{{ s.description || t("explore.noDesc") }}</p>
            <div class="foot muted">{{ t("explore.authorPrefix") }}{{ authorLabel(s) }}</div>
          </div>
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
.explore-page {
  padding-bottom: 8px;
}

.hero {
  margin-bottom: 32px;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: var(--app-text);
  letter-spacing: -0.02em;
}

.hero-sub {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--app-muted);
  line-height: 1.6;
}

.hero-stat {
  font-weight: 600;
  border: 1px solid var(--app-border) !important;
  background: var(--app-surface) !important;
  color: var(--app-primary-deep) !important;
}

.search-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.search-input {
  width: 100%;
  max-width: 560px;
}

.search-input :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: var(--radius-pill);
  box-shadow: 0 0 0 1px var(--app-border) inset;
  background: var(--app-surface);
  padding-left: 14px;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: var(--focus-ring), 0 0 0 1px var(--app-primary-deep) inset;
}

.search-ico {
  color: var(--app-placeholder);
  font-size: 18px;
}

.filters {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}

.filter-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.filter-label {
  font-size: 12px;
  color: var(--app-muted);
}

.author-input {
  width: 180px;
}

.author-input :deep(.el-input__wrapper) {
  min-height: 40px;
  border-radius: var(--radius-control);
}

.cat-radio-group :deep(.el-radio-button__inner) {
  border-radius: 999px !important;
  border: 1px solid var(--app-border-strong) !important;
  box-shadow: none !important;
  padding: 8px 14px;
  font-weight: 500;
}

.cat-radio-group :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 999px !important;
}

.cat-radio-group :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 999px !important;
}

.cat-radio-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: var(--app-primary) !important;
  border-color: var(--app-primary) !important;
  color: #fff !important;
  box-shadow: none !important;
}

.sort-block {
  margin-left: auto;
}

.sort-select {
  width: 140px;
}

.sort-select :deep(.el-select__wrapper) {
  min-height: 40px;
  border-radius: var(--radius-control);
}

.loading {
  padding: 12px 4px;
}

.grid {
  margin-top: 4px;
}

.skill-card {
  height: 100%;
  background: var(--app-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--app-border);
}

.skill-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.skill-card:focus-visible {
  outline: 2px solid var(--app-primary-deep);
  outline-offset: 2px;
}

.skill-hero {
  height: 80px;
  border-radius: var(--radius-card) var(--radius-card) 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.tone-productivity {
  background: linear-gradient(135deg, #0ea5e9 0%, #14b8a6 100%);
}

.tone-security {
  background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
}

.tone-support {
  background: linear-gradient(135deg, #f97316 0%, #fbbf24 100%);
}

.tone-knowledge {
  background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%);
}

.tone-other,
.tone-default {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

.hero-icon {
  width: 40px;
  height: 40px;
  opacity: 0.95;
}

.skill-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  margin-top: 12px;
}

.tags-row {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.desc {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--app-muted);
  flex: 1;
}

.foot {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--app-border);
  font-size: 12px;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .author-input {
    width: 100%;
  }

  .sort-block {
    margin-left: 0;
  }
}
</style>

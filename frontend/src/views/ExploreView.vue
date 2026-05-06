<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchSkills } from "@/api/skills";
import type { Skill } from "@/api/types";

const router = useRouter();

const loading = ref(false);
const allItems = ref<Skill[]>([]);
const query = ref("");
const activeCategory = ref<"all" | "productivity" | "security" | "support" | "knowledge" | "other">("all");
const page = ref(1);
const pageSize = 12;

const STANDARD = new Set(["productivity", "security", "support", "knowledge"]);

function skillCategoryLabel(skill: Skill) {
  return skill.category && skill.category.trim() ? skill.category : "—";
}

function authorLabel(skill: Skill) {
  const id = skill.author_id;
  if (!id) return "—";
  return id.length <= 12 ? id : `…${id.slice(-10)}`;
}

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  return allItems.value.filter((s) => {
    const catOk = (() => {
      const c = (s.category ?? "").toLowerCase();
      if (activeCategory.value === "all") return true;
      if (activeCategory.value === "other") return !c || !STANDARD.has(c);
      return c === activeCategory.value;
    })();
    if (!catOk) return false;
    if (!q) return true;
    const name = (s.name ?? "").toLowerCase();
    const desc = (s.description ?? "").toLowerCase();
    return name.includes(q) || desc.includes(q);
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)));

const paged = computed(() => {
  const start = (page.value - 1) * pageSize;
  return filtered.value.slice(start, start + pageSize);
});

watch([query, activeCategory], () => {
  page.value = 1;
});

watch(filtered, () => {
  if (page.value > totalPages.value) page.value = totalPages.value;
});

async function loadAllPublished() {
  loading.value = true;
  const items: Skill[] = [];
  try {
    let p = 1;
    while (true) {
      const { data } = await fetchSkills({ status: "published", page: p, page_size: 100 });
      items.push(...data.items);
      if (data.items.length === 0 || items.length >= data.total) break;
      p += 1;
    }
    allItems.value = items;
  } catch {
    ElMessage.error("加载市场列表失败");
  } finally {
    loading.value = false;
  }
}

function setCat(v: typeof activeCategory.value) {
  activeCategory.value = v;
}

function goDetail(s: Skill) {
  router.push({ name: "skill-detail", params: { id: s.id } });
}

function text(key: string) {
  const map: Record<string, string> = {
    headline: "应用市场",
    sub: "已上架 Skill 一览，可使用搜索与分类快速定位。",
    searchPh: "按名称或简介搜索…",
    empty: "暂无符合条件的 Skill",
  };
  return map[key] ?? key;
}

const tags: { key: typeof activeCategory.value; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "productivity", label: "productivity" },
  { key: "security", label: "security" },
  { key: "support", label: "support" },
  { key: "knowledge", label: "knowledge" },
  { key: "other", label: "其他" },
];

onMounted(() => void loadAllPublished());
</script>

<template>
  <div>
    <div class="card-panel hero">
      <h1 class="page-title">{{ text("headline") }}</h1>
      <p class="muted">{{ text("sub") }}</p>
      <el-input v-model="query" class="search" clearable :placeholder="text('searchPh')" />
      <div class="tag-row">
        <el-button
          v-for="t in tags"
          :key="t.key"
          size="small"
          :type="activeCategory === t.key ? 'primary' : 'default'"
          plain
          @click="setCat(t.key)"
        >
          {{ t.label }}
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="muted loading">加载中…</div>

    <el-empty v-else-if="filtered.length === 0" :description="text('empty')" />

    <el-row v-else :gutter="16" class="grid">
      <el-col v-for="s in paged" :key="s.id" :xs="24" :sm="12" :md="8" :lg="6">
        <div class="skill-card card-panel" role="button" tabindex="0" @click="goDetail(s)" @keydown.enter.prevent="goDetail(s)">
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

    <div v-if="!loading && filtered.length" class="pager">
      <el-pagination
        v-model:current-page="page"
        background
        layout="prev, pager, next, total"
        :page-size="pageSize"
        :total="filtered.length"
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

.tag-row {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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

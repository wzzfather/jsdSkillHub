import { defineStore } from "pinia";
import { ref } from "vue";
import type { Skill } from "@/api/types";
import { fetchSkills } from "@/api/skills";

export const useSkillsStore = defineStore("skills", () => {
  const published = ref<Skill[]>([]);
  const loading = ref(false);

  async function loadPublished() {
    loading.value = true;
    try {
      const { data } = await fetchSkills({ status: "published", page: 1, page_size: 50 });
      published.value = data.items;
    } finally {
      loading.value = false;
    }
  }

  return { published, loading, loadPublished };
});

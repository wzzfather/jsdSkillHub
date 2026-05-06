import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import { login as loginRequest } from "@/api/auth";
import { fetchPendingReviews } from "@/api/reviews";
import { getJwtSubject } from "@/utils/jwt";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("token"));
  const isAdmin = ref(false);

  const userId = computed(() => getJwtSubject(token.value));

  function setToken(t: string | null) {
    token.value = t;
    if (t) localStorage.setItem("token", t);
    else localStorage.removeItem("token");
    if (!t) isAdmin.value = false;
  }

  async function ensureAdmin(): Promise<void> {
    if (!token.value) {
      isAdmin.value = false;
      return;
    }
    try {
      await fetchPendingReviews();
      isAdmin.value = true;
    } catch {
      isAdmin.value = false;
    }
  }

  async function login(payload: { username?: string; email?: string; password: string }) {
    const { data } = await loginRequest(payload);
    setToken(data.access_token);
    await ensureAdmin();
  }

  function clear() {
    setToken(null);
  }

  watch(
    token,
    () => {
      void ensureAdmin();
    },
    { immediate: true },
  );

  return { token, isAdmin, userId, login, clear, ensureAdmin, setToken };
});

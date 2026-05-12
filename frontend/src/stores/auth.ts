import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import { fetchCurrentUser, login as loginRequest } from "@/api/auth";
import { fetchPendingReviews } from "@/api/reviews";
import { getJwtSubject } from "@/utils/jwt";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("token"));
  const isAdmin = ref(false);
  const avatarUrl = ref<string | null>(null);
  const profileUsername = ref<string | null>(null);

  const userId = computed(() => getJwtSubject(token.value));

  const headerInitial = computed(() => {
    const u = profileUsername.value?.trim() ?? "";
    const c = u.charAt(0);
    return c ? c.toUpperCase() : "?";
  });

  async function refreshMe(): Promise<void> {
    if (!token.value) {
      avatarUrl.value = null;
      profileUsername.value = null;
      return;
    }
    try {
      const { data } = await fetchCurrentUser();
      avatarUrl.value = data.avatar_url ? `${data.avatar_url}?t=${Date.now()}` : null;
      profileUsername.value = data.username;
    } catch {
      avatarUrl.value = null;
      profileUsername.value = null;
    }
  }

  function setToken(t: string | null) {
    token.value = t;
    if (t) localStorage.setItem("token", t);
    else localStorage.removeItem("token");
    if (!t) {
      isAdmin.value = false;
      avatarUrl.value = null;
      profileUsername.value = null;
    }
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
      void refreshMe();
    },
    { immediate: true },
  );

  return {
    token,
    isAdmin,
    userId,
    avatarUrl,
    profileUsername,
    headerInitial,
    login,
    clear,
    ensureAdmin,
    refreshMe,
    setToken,
  };
});

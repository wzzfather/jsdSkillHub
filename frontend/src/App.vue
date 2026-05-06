<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const isAuthed = computed(() => !!auth.token);
const isAdmin = computed(() => auth.isAdmin);

function logout() {
  auth.clear();
  router.push({ name: "explore" });
}

function navClass(name: string | string[]) {
  const names = Array.isArray(name) ? name : [name];
  const hit = names.includes(String(route.name));
  return ["nav-link", ...(hit ? ["is-active"] : [])];
}

function goBrand() {
  router.push(auth.token ? { name: "dashboard" } : { name: "explore" });
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="app-brand" role="button" tabindex="0" @click="goBrand" @keydown.enter.prevent="goBrand">
        Skill Store
      </div>
      <nav class="app-nav">
        <el-button text :class="navClass(['explore', 'skill-detail'])" @click="router.push({ name: 'explore' })">浏览</el-button>

        <template v-if="!isAuthed">
          <el-button text :class="navClass('login')" @click="router.push({ name: 'login' })">
            登录
          </el-button>
          <el-button text :class="navClass('register')" @click="router.push({ name: 'register' })">
            注册
          </el-button>
        </template>

        <template v-else>
          <el-button text :class="navClass('submit')" @click="router.push({ name: 'submit' })">提交应用</el-button>
          <el-button text :class="navClass('my-apps')" @click="router.push({ name: 'my-apps' })">我的应用</el-button>
          <el-button v-if="isAdmin" text :class="navClass('review')" @click="router.push({ name: 'review' })">
            审批工作台
          </el-button>
          <el-button text :class="navClass('dashboard')" @click="router.push({ name: 'dashboard' })">看板</el-button>
          <el-button text class="nav-link" @click="logout">退出</el-button>
        </template>
      </nav>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

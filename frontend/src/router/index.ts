import { createRouter, createWebHistory } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const LoginView = () => import("@/views/LoginView.vue");
const RegisterView = () => import("@/views/RegisterView.vue");
const VerifyEmailView = () => import("@/views/VerifyEmailView.vue");
const ExploreView = () => import("@/views/ExploreView.vue");
const SkillDetailView = () => import("@/views/SkillDetailView.vue");
const SubmitView = () => import("@/views/SubmitView.vue");
const MyAppsView = () => import("@/views/MyAppsView.vue");
const ReviewView = () => import("@/views/ReviewView.vue");
const DashboardView = () => import("@/views/DashboardView.vue");

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: () => {
        const auth = useAuthStore();
        return auth.token ? "/dashboard" : "/explore";
      },
    },
    { path: "/login", name: "login", component: LoginView, meta: { guest: true } },
    { path: "/register", name: "register", component: RegisterView, meta: { guest: true } },
    { path: "/verify-email", name: "verify-email", component: VerifyEmailView },
    { path: "/explore", name: "explore", component: ExploreView },
    {
      path: "/explore/:id",
      name: "skill-detail",
      component: SkillDetailView,
      props: true,
    },
    { path: "/submit", name: "submit", component: SubmitView, meta: { requiresAuth: true } },
    { path: "/my-apps", name: "my-apps", component: MyAppsView, meta: { requiresAuth: true } },
    {
      path: "/review",
      name: "review",
      component: ReviewView,
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    { path: "/dashboard", name: "dashboard", component: DashboardView, meta: { requiresAuth: true } },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (to.meta.requiresAdmin && auth.token) {
    await auth.ensureAdmin();
    if (!auth.isAdmin) {
      ElMessage.warning("需要管理员权限");
      return { name: "explore" };
    }
  }

  if (to.meta.guest && auth.token && (to.name === "login" || to.name === "register")) {
    return { name: "dashboard" };
  }

  return true;
});

export default router;

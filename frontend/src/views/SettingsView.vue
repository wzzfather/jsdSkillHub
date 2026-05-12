<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import "vue-picture-cropper/style.css";
import "cropperjs/dist/cropper.css";
import { useCropper } from "vue-picture-cropper";
import { useLocale } from "@/locales";
import { useAuthStore } from "@/stores/auth";
import {
  changePassword,
  fetchCurrentUser,
  sendCode,
  updateProfile,
  uploadAvatar,
} from "@/api/auth";
import type { UserMeResponse } from "@/api/types";

const { t, locale, setLocale } = useLocale();
const auth = useAuthStore();

const activeTab = ref("profile");
const tabPosition = ref<"left" | "top">("left");
let mq: MediaQueryList | null = null;

function syncTabPosition() {
  tabPosition.value = window.matchMedia("(max-width: 768px)").matches ? "top" : "left";
}

function onMqChange() {
  syncTabPosition();
}

const profileLoading = ref(false);
const profileSaving = ref(false);
const me = ref<UserMeResponse | null>(null);
const username = ref("");
const email = ref("");

const passwordSaving = ref(false);
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const avatarUploading = ref(false);

/* ---- 裁切弹窗 ---- */
const cropDialogVisible = ref(false);
const cropImageSrc = ref("");

/** 头像 URL 加 cache-bust 参数，避免上传后浏览器缓存旧图 */
const avatarDisplayUrl = computed(() => {
  const url = me.value?.avatar_url;
  if (!url) return "";
  return `${url}?t=${Date.now()}`;
});

const [CropperComponent, cropper] = useCropper(
  computed(() => ({
    img: cropImageSrc.value,
    options: {
      viewMode: 1,
      dragMode: "move" as const,
      aspectRatio: 1,
      autoCropArea: 0.85,
      cropBoxResizable: true,
      cropBoxMovable: false,
    },
  })),
);

const fileInput = ref<HTMLInputElement | null>(null);

/** 偏好 Tab：开关 ON = 暗色（与 document.documentElement.dark 一致） */
const prefDark = ref(false);

const avatarLetter = computed(() => {
  const u = username.value.trim();
  const c = u.charAt(0);
  return c ? c.toUpperCase() : "?";
});

const isAdminRole = computed(() => me.value?.role === "admin");

/** 邮箱校验展示：区分未填写、未保存变更、已保存未验证、已验证 */
const emailVerificationUi = computed(() => {
  const cur = email.value.trim();
  if (!cur) return "empty" as const;
  const saved = (me.value?.email ?? "").trim();
  if (cur !== saved) return "pending" as const;
  return me.value?.email_verified ? ("verified" as const) : ("unverified" as const);
});

function formatTime(iso?: string | null) {
  if (!iso) return t("common.emDash");
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function apiErrorDetail(err: unknown): string {
  const e = err as { response?: { data?: { detail?: unknown } } };
  const d = e.response?.data?.detail;
  if (typeof d === "string") return d;
  if (d && typeof d === "object" && "detail" in d) {
    const inner = (d as { detail?: unknown }).detail;
    if (typeof inner === "string") return inner;
  }
  return t("detail.errOp");
}

async function loadProfile() {
  profileLoading.value = true;
  try {
    const { data } = await fetchCurrentUser();
    me.value = data;
    username.value = data.username;
    email.value = data.email ?? "";
  } catch (e) {
    const msg = apiErrorDetail(e);
    ElMessage.error(msg === t("detail.errOp") ? t("settings.loadFail") : msg);
    me.value = null;
  } finally {
    profileLoading.value = false;
  }
}

function validateUsername(): boolean {
  const u = username.value.trim();
  if (u.length < 2 || u.length > 64) {
    ElMessage.warning(t("settings.usernameInvalid"));
    return false;
  }
  return true;
}

async function saveProfile() {
  if (!validateUsername()) return;
  profileSaving.value = true;
  try {
    const trimmedMail = email.value.trim();
    const payload = {
      username: username.value.trim(),
      email: trimmedMail ? trimmedMail : null,
    };
    const { data } = await updateProfile(payload);
    me.value = data;
    username.value = data.username;
    email.value = data.email ?? "";
    await auth.refreshMe();
    ElMessage.success(t("settings.saveSuccess"));
  } catch (e) {
    ElMessage.error(apiErrorDetail(e));
  } finally {
    profileSaving.value = false;
  }
}

function passwordStrongEnough(p: string): boolean {
  if (p.length < 8) return false;
  if (!/[A-Za-z]/.test(p)) return false;
  if (!/\d/.test(p)) return false;
  return true;
}

async function submitPasswordChange() {
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.warning(t("settings.passwordMismatch"));
    return;
  }
  if (!passwordStrongEnough(newPassword.value)) {
    ElMessage.warning(t("settings.passwordWeak"));
    return;
  }
  passwordSaving.value = true;
  try {
    const { data } = await changePassword({
      current_password: currentPassword.value,
      new_password: newPassword.value,
    });
    auth.setToken(data.access_token);
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
    ElMessage.success(t("settings.changePasswordSuccess"));
  } catch (e) {
    ElMessage.error(apiErrorDetail(e));
  } finally {
    passwordSaving.value = false;
  }
}

function beforeAvatarUpload(file: File) {
  const allowedMime = ["image/jpeg", "image/png", "image/webp"];
  const okExt = /\.(jpe?g|png|webp)$/i.test(file.name);
  if (!okExt) {
    ElMessage.warning(t("settings.avatarFormat"));
    return false;
  }
  if (file.type && !allowedMime.includes(file.type)) {
    ElMessage.warning(t("settings.avatarFormat"));
    return false;
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning(t("settings.avatarTooLarge"));
    return false;
  }
  return true;
}

function triggerAvatarPick() {
  fileInput.value?.click();
}

function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  if (!beforeAvatarUpload(file)) {
    target.value = "";
    return;
  }
  const reader = new FileReader();
  reader.onload = (ev) => {
    cropImageSrc.value = ev.target?.result as string;
    cropDialogVisible.value = true;
  };
  reader.readAsDataURL(file);
  target.value = "";
}

async function confirmCrop() {
  const file = await cropper.getFile({
    width: 256,
    height: 256,
    fillColor: "#fff",
    fileName: "avatar.webp",
  });
  if (!file) {
    ElMessage.error(t("settings.avatarCropFail"));
    return;
  }
  cropDialogVisible.value = false;
  avatarUploading.value = true;
  try {
    await uploadAvatar(file);
    ElMessage.success(t("settings.avatarSuccess"));
    const { data } = await fetchCurrentUser();
    me.value = data;
    username.value = data.username;
    email.value = data.email ?? "";
    await auth.refreshMe();
  } catch (e) {
    ElMessage.error(apiErrorDetail(e));
  } finally {
    avatarUploading.value = false;
  }
}

function cancelCrop() {
  cropDialogVisible.value = false;
  cropImageSrc.value = "";
}

async function resendVerification() {
  if (emailVerificationUi.value !== "unverified") {
    ElMessage.warning(t("settings.emailVerifySaveFirst"));
    return;
  }
  const em = email.value.trim();
  try {
    await sendCode(em);
    ElMessage.success(t("settings.resendSuccess"));
  } catch (e) {
    ElMessage.error(apiErrorDetail(e));
  }
}

function onLanguageChange(lang: string | number | boolean | undefined) {
  const raw = String(lang ?? "");
  if (raw !== "zh" && raw !== "en") return;
  setLocale(raw);
  ElMessage.success(t("settings.languageChanged"));
}

function syncPrefDarkFromDom() {
  prefDark.value = document.documentElement.classList.contains("dark");
}

function onThemeSwitch(isDark: boolean | string | number) {
  const on = Boolean(isDark);
  const root = document.documentElement;
  if (on) {
    root.classList.add("dark");
    localStorage.setItem("theme", "dark");
  } else {
    root.classList.remove("dark");
    localStorage.setItem("theme", "light");
  }
  prefDark.value = on;
  ElMessage.success(t("settings.themeChanged"));
}

watch(activeTab, (name) => {
  if (name === "preferences") syncPrefDarkFromDom();
});

onMounted(() => {
  syncTabPosition();
  mq = window.matchMedia("(max-width: 768px)");
  mq.addEventListener("change", onMqChange);
  void loadProfile();
  syncPrefDarkFromDom();
});

onUnmounted(() => {
  mq?.removeEventListener("change", onMqChange);
});
</script>

<template>
  <div class="settings-page">
    <header class="page-head card-panel">
      <h2 class="page-heading">{{ t("settings.title") }}</h2>
    </header>

    <div v-loading="profileLoading" class="settings-shell card-panel">
      <el-tabs v-model="activeTab" class="settings-tabs" :tab-position="tabPosition">
        <el-tab-pane :label="t('settings.profile')" name="profile">
          <div class="tab-body">
            <div class="avatar-block">
              <input
                ref="fileInput"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                class="avatar-file-input"
                @change="onFileSelected"
              />
              <div
                class="avatar-lg"
                role="button"
                tabindex="0"
                v-loading="avatarUploading"
                :aria-label="t('settings.avatarUpload')"
                @click="triggerAvatarPick"
                @keydown.enter.prevent="triggerAvatarPick"
                @keydown.space.prevent="triggerAvatarPick"
              >
                <img v-if="me?.avatar_url" :src="avatarDisplayUrl" class="avatar-photo" alt="" />
                <template v-else>{{ avatarLetter }}</template>
              </div>
              <span class="muted avatar-v2">{{ t("settings.avatarUpload") }}</span>
            </div>

            <el-form label-position="top" class="profile-form" @submit.prevent>
              <el-form-item :label="t('settings.username')">
                <el-input v-model="username" maxlength="64" show-word-limit />
              </el-form-item>
              <el-form-item :label="t('settings.email')">
                <el-input v-model="email" type="email" autocomplete="email" />
              </el-form-item>
              <el-form-item :label="t('settings.emailVerification')">
                <template v-if="emailVerificationUi === 'empty'">
                  <span class="muted">{{ t("common.emDash") }}</span>
                </template>
                <template v-else-if="emailVerificationUi === 'pending'">
                  <el-tag type="info" effect="plain">{{ t("settings.emailWillVerify") }}</el-tag>
                </template>
                <template v-else-if="emailVerificationUi === 'verified'">
                  <el-tag type="success" effect="plain">{{ t("settings.emailVerified") }}</el-tag>
                </template>
                <template v-else>
                  <div class="verify-row">
                    <el-tag type="warning" effect="plain">{{ t("settings.emailNotVerified") }}</el-tag>
                    <el-link type="primary" :underline="false" @click="resendVerification">
                      {{ t("settings.resendVerify") }}
                    </el-link>
                  </div>
                </template>
              </el-form-item>
              <el-form-item :label="t('settings.role')">
                <el-tag :type="isAdminRole ? 'danger' : 'info'" effect="plain">
                  {{ isAdminRole ? t("settings.roleAdmin") : t("settings.roleUser") }}
                </el-tag>
              </el-form-item>
              <el-form-item :label="t('settings.createdAt')">
                <span>{{ formatTime(me?.created_at) }}</span>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="profileSaving" @click="saveProfile">
                  {{ t("settings.save") }}
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('settings.security')" name="security">
          <div class="tab-body">
            <el-form label-position="top" class="security-form" @submit.prevent>
              <el-form-item :label="t('settings.currentPassword')">
                <el-input v-model="currentPassword" type="password" show-password autocomplete="current-password" />
              </el-form-item>
              <el-form-item :label="t('settings.newPassword')">
                <el-input v-model="newPassword" type="password" show-password autocomplete="new-password" />
                <div class="muted field-hint">{{ t("settings.passwordHint") }}</div>
              </el-form-item>
              <el-form-item :label="t('settings.confirmPassword')">
                <el-input v-model="confirmPassword" type="password" show-password autocomplete="new-password" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="passwordSaving" @click="submitPasswordChange">
                  {{ t("settings.changePassword") }}
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('settings.preferences')" name="preferences">
          <div class="tab-body">
            <div class="pref-block">
              <div class="pref-label">{{ t("settings.language") }}</div>
              <el-radio-group :model-value="locale" @change="onLanguageChange">
                <el-radio-button label="zh">{{ t("lang.zh") }}</el-radio-button>
                <el-radio-button label="en">{{ t("lang.en") }}</el-radio-button>
              </el-radio-group>
            </div>
            <div class="pref-block">
              <div class="pref-label">{{ t("settings.theme") }}</div>
              <el-switch
                :model-value="prefDark"
                :active-text="t('settings.themeDark')"
                :inactive-text="t('settings.themeLight')"
                @change="onThemeSwitch"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 头像裁切弹窗 -->
    <el-dialog
      v-model="cropDialogVisible"
      :title="t('settings.avatarCropTitle')"
      width="420px"
      :close-on-click-modal="false"
      @close="cancelCrop"
    >
      <div class="crop-container">
        <CropperComponent :box-style="{ width: '100%', height: '100%' }" />
      </div>
      <template #footer>
        <el-button @click="cancelCrop">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="avatarUploading" @click="confirmCrop">
          {{ t('settings.avatarCropConfirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-head {
  padding: 24px;
}

.page-heading {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
}

.settings-shell {
  padding: 16px 24px 24px;
  min-height: 320px;
}

.settings-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}

.tab-body {
  max-width: 520px;
}

.avatar-block {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.avatar-file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.avatar-lg:focus-visible {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--app-primary) 35%, transparent);
}

.avatar-lg {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--app-primary) 0%, var(--app-primary-deep) 100%);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  flex-shrink: 0;
  cursor: pointer;
  overflow: hidden;
}

.avatar-photo {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.avatar-v2 {
  font-size: 13px;
}

.verify-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.field-hint {
  margin-top: 6px;
  font-size: 12px;
}

.pref-block {
  margin-bottom: 24px;
}

.pref-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
  margin-bottom: 10px;
}

.crop-container {
  width: 100%;
  height: 360px;
  overflow: hidden;
  border-radius: 8px;
  background: #f5f5f5;
}

@media (max-width: 768px) {
  .settings-shell {
    padding: 12px 16px 20px;
  }

  .settings-tabs :deep(.el-tabs__header) {
    margin-bottom: 12px;
  }

  .tab-body {
    max-width: none;
  }
}
</style>

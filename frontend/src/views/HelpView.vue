<script setup lang="ts">
import { computed } from "vue";
import { ElMessage } from "element-plus";
import { useLocale } from "@/locales";

const { t } = useLocale();

/** 与 SkillDetailView 一致：使用 Clipboard API 写入剪贴板（navigator.clipboard.writeText） */
async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success(t("detail.cliInstallCopied"));
  } catch {
    ElMessage.error(t("detail.cliInstallCopyFail"));
  }
}

const commandRows = computed(() =>
  [
    { cmdKey: "help.cmd.upgrade", descKey: "help.desc.upgrade" },
    { cmdKey: "help.cmd.login", descKey: "help.desc.login" },
    { cmdKey: "help.cmd.search", descKey: "help.desc.search" },
    { cmdKey: "help.cmd.install", descKey: "help.desc.install" },
    { cmdKey: "help.cmd.list", descKey: "help.desc.list" },
    { cmdKey: "help.cmd.update", descKey: "help.desc.update" },
    { cmdKey: "help.cmd.uninstall", descKey: "help.desc.uninstall" },
    { cmdKey: "help.cmd.info", descKey: "help.desc.info" },
    { cmdKey: "help.cmd.configSet", descKey: "help.desc.configSet" },
    { cmdKey: "help.cmd.configShow", descKey: "help.desc.configShow" },
  ].map((row) => ({
    cmd: t(row.cmdKey),
    desc: t(row.descKey),
  })),
);
</script>

<template>
  <div class="help-page">
    <h1 class="help-title">{{ t("help.title") }}</h1>

    <el-card class="help-card" shadow="never">
      <template #header>
        <span class="card-head">{{ t("help.card.install") }}</span>
      </template>

      <el-alert type="info" :closable="false" show-icon class="help-alert">
        {{ t("help.prereq") }}
      </el-alert>

      <div class="code-wrap">
        <el-button type="primary" plain size="small" class="copy-btn" @click="copyText(t('help.cmd.pip'))">
          {{ t("detail.cliInstallCopy") }}
        </el-button>
        <pre class="code-pre"><code>{{ t("help.cmd.pip") }}</code></pre>
      </div>
      <p class="help-note">{{ t("help.install.afterCmd") }}</p>

      <p class="help-text">{{ t("help.install.intranet") }}</p>

      <div class="code-wrap">
        <el-button type="primary" plain size="small" class="copy-btn" @click="copyText(t('help.cmd.gitpip'))">
          {{ t("detail.cliInstallCopy") }}
        </el-button>
        <pre class="code-pre"><code>{{ t("help.cmd.gitpip") }}</code></pre>
      </div>
      <p class="help-note">{{ t("help.install.afterCmd") }}</p>
    </el-card>

    <el-divider />

    <el-card class="help-card" shadow="never">
      <template #header>
        <span class="card-head">{{ t("help.card.config") }}</span>
      </template>

      <el-alert type="warning" :closable="false" show-icon class="help-alert">
        {{ t("help.config.note") }}
      </el-alert>

      <p class="label-strong">{{ t("help.config.lanLabel") }}</p>
      <div class="code-wrap">
        <el-button type="primary" plain size="small" class="copy-btn" @click="copyText(t('help.cmd.configLan'))">
          {{ t("detail.cliInstallCopy") }}
        </el-button>
        <pre class="code-pre"><code>{{ t("help.cmd.configLan") }}</code></pre>
      </div>
      <el-alert type="success" :closable="false" :show-icon="false" class="help-alert help-alert-config">
        {{ t("help.config.saved") }}
      </el-alert>

      <p class="label-strong">{{ t("help.config.pubLabel") }}</p>
      <div class="code-wrap">
        <el-button type="primary" plain size="small" class="copy-btn" @click="copyText(t('help.cmd.configPub'))">
          {{ t("detail.cliInstallCopy") }}
        </el-button>
        <pre class="code-pre"><code>{{ t("help.cmd.configPub") }}</code></pre>
      </div>
      <el-alert type="success" :closable="false" :show-icon="false" class="help-alert help-alert-config">
        {{ t("help.config.saved") }}
      </el-alert>
    </el-card>

    <el-divider />

    <el-card class="help-card" shadow="never">
      <template #header>
        <span class="card-head">{{ t("help.card.commands") }}</span>
      </template>

      <div v-for="(row, idx) in commandRows" :key="idx" class="cmd-row">
        <div class="code-wrap">
          <el-button type="primary" plain size="small" class="copy-btn" @click="copyText(row.cmd)">
            {{ t("detail.cliInstallCopy") }}
          </el-button>
          <pre class="code-pre"><code>{{ row.cmd }}</code></pre>
        </div>
        <p class="cmd-desc">{{ row.desc }}</p>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.help-page {
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 24px;
}

.help-title {
  margin: 0 0 24px;
  font-size: 20px;
  font-weight: 600;
  color: var(--app-text);
}

.help-card {
  border-radius: var(--radius-card);
  border: 1px solid var(--app-border);
}

.help-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--app-border);
}

.help-card :deep(.el-card__body) {
  padding: 20px;
}

.card-head {
  font-size: 16px;
  font-weight: 600;
  color: var(--app-text);
}

.help-alert {
  margin-bottom: 16px;
}

.help-text {
  margin: 16px 0 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--app-text);
}

.help-note {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--app-muted);
}

.help-alert-config {
  margin-bottom: 16px;
}

.label-strong {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}

.label-strong:first-of-type {
  margin-top: 0;
}

.code-wrap {
  position: relative;
  margin-bottom: 12px;
  border-radius: var(--radius-control);
  background: #161b22;
  border: 1px solid var(--app-border-strong);
  padding: 40px 14px 14px;
}

html.dark .code-wrap {
  background: #0d1117;
  border-color: var(--app-border);
}

.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
  font-weight: 600;
}

.code-pre {
  margin: 0;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #e6edf3;
}

.cmd-row {
  margin-bottom: 18px;
}

.cmd-row:last-child {
  margin-bottom: 0;
}

.cmd-desc {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--app-muted);
}

.help-page :deep(.el-divider) {
  margin: 24px 0;
  border-color: var(--app-border);
}
</style>

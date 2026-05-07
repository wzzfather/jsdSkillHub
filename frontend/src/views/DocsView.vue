<script setup lang="ts">
import { useLocale } from "@/locales";

const { t } = useLocale();
</script>

<template>
  <div class="docs-page">
    <h1 class="docs-title">{{ t("docs.title") }}</h1>

    <section class="docs-section">
      <h2>{{ t("docs.intro.title") }}</h2>
      <p>{{ t("docs.intro.p1") }}</p>
      <p>{{ t("docs.intro.p2") }}</p>
    </section>

    <section class="docs-section">
      <h2>{{ t("docs.guide.title") }}</h2>

      <h3>{{ t("docs.guide.submit.title") }}</h3>
      <ol>
        <li>{{ t("docs.guide.submit.step1") }}</li>
        <li>{{ t("docs.guide.submit.step2") }}</li>
        <li>{{ t("docs.guide.submit.step3") }}</li>
        <li>{{ t("docs.guide.submit.step4") }}</li>
      </ol>

      <h3>{{ t("docs.guide.review.title") }}</h3>
      <p>{{ t("docs.guide.review.p1") }}</p>
      <ul>
        <li>{{ t("docs.guide.review.semgrep") }}</li>
        <li>{{ t("docs.guide.review.clamav") }}</li>
        <li>{{ t("docs.guide.review.llm") }}</li>
      </ul>
      <p>{{ t("docs.guide.review.p2") }}</p>

      <h3>{{ t("docs.guide.install.title") }}</h3>
      <p>{{ t("docs.guide.install.p1") }}</p>
    </section>

    <section class="docs-section">
      <h2>{{ t("docs.scanning.title") }}</h2>
      <p>{{ t("docs.scanning.p1") }}</p>
      <div class="scan-table-wrapper">
        <table class="scan-table">
          <thead>
            <tr>
              <th>{{ t("docs.scanning.layer") }}</th>
              <th>{{ t("docs.scanning.tool") }}</th>
              <th>{{ t("docs.scanning.desc") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1</td>
              <td>Semgrep</td>
              <td>{{ t("docs.scanning.semgrepDesc") }}</td>
            </tr>
            <tr>
              <td>2</td>
              <td>ClamAV</td>
              <td>{{ t("docs.scanning.clamavDesc") }}</td>
            </tr>
            <tr>
              <td>3</td>
              <td>LLM (Qwen)</td>
              <td>{{ t("docs.scanning.llmDesc") }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="docs-section">
      <h2>{{ t("docs.faq.title") }}</h2>
      <div class="faq-item">
        <h4>{{ t("docs.faq.q1") }}</h4>
        <p>{{ t("docs.faq.a1") }}</p>
      </div>
      <div class="faq-item">
        <h4>{{ t("docs.faq.q2") }}</h4>
        <p>{{ t("docs.faq.a2") }}</p>
      </div>
      <div class="faq-item">
        <h4>{{ t("docs.faq.q3") }}</h4>
        <p>{{ t("docs.faq.a3") }}</p>
      </div>
    </section>

    <section class="docs-section">
      <h2>{{ t("docs.arch.title") }}</h2>
      <p>{{ t("docs.arch.p1") }}</p>
      <div class="arch-table-wrapper">
        <table class="arch-table">
          <thead>
            <tr>
              <th>{{ t("docs.arch.layer") }}</th>
              <th>{{ t("docs.arch.tech") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>{{ t("docs.arch.frontend") }}</td><td>Vue 3 + TypeScript + Element Plus</td></tr>
            <tr><td>{{ t("docs.arch.backend") }}</td><td>FastAPI + SQLAlchemy (async)</td></tr>
            <tr><td>{{ t("docs.arch.database") }}</td><td>PostgreSQL 16</td></tr>
            <tr><td>{{ t("docs.arch.storage") }}</td><td>MinIO (S3 compatible)</td></tr>
            <tr><td>{{ t("docs.arch.search") }}</td><td>OpenSearch</td></tr>
            <tr><td>{{ t("docs.arch.security") }}</td><td>Semgrep + ClamAV + LLM</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.docs-page {
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 0;
}

.docs-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--app-text);
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--app-border);
}

.docs-section {
  margin-bottom: 32px;
}

.docs-section h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--app-text);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--app-border);
}

.docs-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--app-text);
  margin: 20px 0 8px;
}

.docs-section p {
  color: var(--app-text);
  line-height: 1.7;
  margin-bottom: 8px;
}

.docs-section ol,
.docs-section ul {
  color: var(--app-text);
  line-height: 1.8;
  padding-left: 24px;
  margin-bottom: 12px;
}

.scan-table-wrapper,
.arch-table-wrapper {
  overflow-x: auto;
  margin: 12px 0;
}

.scan-table,
.arch-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.scan-table th,
.scan-table td,
.arch-table th,
.arch-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--app-border);
  color: var(--app-text);
}

.scan-table th,
.arch-table th {
  background: var(--app-surface);
  font-weight: 600;
  color: var(--app-text);
}

.faq-item {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--app-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.faq-item h4 {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-primary);
  margin-bottom: 6px;
}

.faq-item p {
  font-size: 14px;
  color: var(--app-text);
  line-height: 1.6;
  margin: 0;
}
</style>

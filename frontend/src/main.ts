import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import "./styles/variables.css";

import App from "./App.vue";
import router from "./router";
import "./styles/global.css";

import { setMessages, setLocale, updateMessages } from "./locales";
import zh from "./locales/zh";
import en from "./locales/en";

// Initialize i18n: start with zh as base, then overlay selected locale
const saved = (localStorage.getItem("locale") as "zh" | "en") || "zh";
setMessages({ ...zh, ...en });
if (saved === "en") {
  updateMessages(en);
}
setLocale(saved);

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.mount("#app");

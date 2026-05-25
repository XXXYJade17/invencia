# 07 —— 前端详细设计

> 版本：v1.0
> 日期：2026-05-24
> 依赖：architecture.md 三、06-api-specs.md

---

## 一、技术方案

- 纯 HTML5 + CSS3 + Vanilla JS（ES Modules）
- 无构建工具，无框架
- SPA 模式，Hash 路由
- 字体：使用系统默认中文字体栈

---

## 二、HTML 页面骨架

### 2.1 index.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>无敌 Invencia —— 千人千命，天道为笔</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <!-- 主视图容器 -->
  <main id="app">
    <!-- 动态渲染页面内容 -->
  </main>

  <!-- 弹窗层（z-index 高于 main） -->
  <div id="modal-overlay" class="modal-overlay hidden">
    <div id="modal-container" class="modal-container">
      <!-- 动态渲染弹窗内容 -->
    </div>
  </div>

  <!-- Toast 通知 -->
  <div id="toast" class="toast hidden"></div>

  <script type="module" src="js/app.js"></script>
</body>
</html>
```

---

## 三、CSS 关键样式

### 3.1 设计基调

| 属性 | 值 |
|------|-----|
| 背景色 | #0a0a0a（极深黑） |
| 主文字色 | #d4c5a9（仿古纸暖黄） |
| 强调色 | #c9a96e（暗金） |
| 危险/警告色 | #8b3a3a（暗红） |
| 成功色 | #4a7c59（墨绿） |
| 字体 | "Noto Serif SC", "Source Han Serif SC", "SimSun", serif |
| 正文字号 | 18px / line-height: 2 |

### 3.2 核心样式

```css
/* 全局重置 */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: #0a0a0a;
  color: #d4c5a9;
  font-family: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
  font-size: 18px;
  line-height: 2;
  min-height: 100vh;
}

/* 主页 Landing */
.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  text-align: center;
}

.landing h1 {
  font-size: 4rem;
  font-weight: 400;
  letter-spacing: 0.3em;
  color: #c9a96e;
  margin-bottom: 0.5rem;
}

.landing .subtitle {
  font-size: 1.2rem;
  color: #8a7a6a;
  letter-spacing: 0.5em;
  margin-bottom: 3rem;
}

/* 游戏主界面 */
.game-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  height: 100vh;
}

.chat-area {
  display: flex;
  flex-direction: column;
  padding: 2rem;
  overflow-y: auto;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 1rem;
}

.input-area {
  display: flex;
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid #2a2a2a;
}

.input-area textarea {
  flex: 1;
  background: #1a1a1a;
  color: #d4c5a9;
  border: 1px solid #3a3a3a;
  padding: 0.75rem;
  font: inherit;
  resize: none;
  min-height: 60px;
}

/* 角色面板侧栏 */
.char-panel {
  background: #111;
  border-left: 1px solid #2a2a2a;
  padding: 2rem 1.5rem;
  overflow-y: auto;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: #1a1a1a;
  border: 1px solid #3a3a3a;
  padding: 2rem;
  max-width: 480px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

/* 按钮 */
.btn {
  padding: 0.75rem 2rem;
  border: 1px solid #c9a96e;
  background: transparent;
  color: #c9a96e;
  font: inherit;
  font-size: 1rem;
  cursor: pointer;
  letter-spacing: 0.2em;
  transition: background 0.3s, color 0.3s;
}

.btn:hover {
  background: #c9a96e;
  color: #0a0a0a;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Loading */
.loading-spinner {
  width: 40px;
  height: 40px;
  border: 2px solid #3a3a3a;
  border-top-color: #c9a96e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hidden { display: none !important; }
```

---

## 四、JS 模块详解

### 4.1 应用入口（app.js）

```javascript
import { initRouter } from "./router.js";
import { initModals } from "./modals/index.js";

document.addEventListener("DOMContentLoaded", function() {
  initRouter();
  initModals();
});
```

### 4.2 路由（router.js）

```javascript
import { renderHome } from "./pages/home.js";
import { renderGame } from "./pages/game.js";
import { isLoggedIn } from "./auth.js";
import { showLoginModal } from "./modals/login.js";

const routes = {
  "#/": renderHome,
  "#/game": renderGame
};

const PROTECTED = ["#/game"];

export function initRouter() {
  window.addEventListener("hashchange", handleRoute);
  handleRoute();
}

function handleRoute() {
  const hash = window.location.hash || "#/";
  const base = hash.split("?")[0];

  if (PROTECTED.some(p => base.startsWith(p)) && !isLoggedIn()) {
    window.location.hash = "#/";
    showLoginModal();
    return;
  }

  const render = routes[base];
  if (render) render();
}

export function navigate(hash) {
  window.location.hash = hash;
}
```

### 4.3 主页（pages/home.js）

> 渲染世界列表 + 示例叙事 + "开始修仙"按钮。核心逻辑见下方。

```javascript
import { apiFetch } from "../api.js";
import { isLoggedIn } from "../auth.js";
import { showLoginModal } from "../modals/login.js";
import { showCharListModal } from "../modals/char-list.js";

export async function renderHome() {
  const res = await apiFetch("/api/worlds");
  if (!res) return;
  const worlds = res.data.worlds;

  let cardsHtml = "";
  for (const w of worlds) {
    cardsHtml += <div class="world-card"><h2>{w.display_name}</h2><p>{w.description.slice(0, 100)}...</p></div>;
  }

  const app = document.getElementById("app");
  app.innerHTML = 
    <div class="landing">
      <h1>无敌</h1>
      <p class="subtitle">INVENCIA · 千人千命，天道为笔</p>
      <div class="world-list">{cardsHtml}</div>
      <button class="btn btn-start" id="btn-start">开始修仙</button>
    </div>;

  document.getElementById("btn-start").addEventListener("click", function() {
    if (isLoggedIn()) {
      showCharListModal();
    } else {
      showLoginModal();
    }
  });
}
```

### 4.4 游戏界面（pages/game.js）

```javascript
import { apiFetch } from "../api.js";

let characterId = null;

export function renderGame() {
  const params = new URLSearchParams(location.hash.split("?")[1]);
  characterId = params.get("id");
  if (!characterId) return;

  const app = document.getElementById("app");
  app.innerHTML = 
    <div class="game-layout">
      <div class="chat-area">
        <div class="chat-messages" id="chat-messages"></div>
        <div class="input-area">
          <textarea id="player-input" placeholder="输入你的行动..."></textarea>
          <button class="btn" id="btn-send">天道</button>
        </div>
      </div>
      <aside class="char-panel" id="char-panel"></aside>
    </div>;

  loadHistory();
  loadCharPanel();
  bindInput();
}

async function loadHistory() {
  const url = "/api/game/" + characterId + "/messages?limit=50";
  const res = await apiFetch(url);
  if (!res) return;
  const container = document.getElementById("chat-messages");
  for (const msg of res.data.messages) {
    appendMessage(msg);
  }
  container.scrollTop = container.scrollHeight;
}

function appendMessage(msg) {
  const el = document.createElement("div");
  el.className = "message message-" + msg.role;
  el.innerHTML = "<p>" + msg.content.replace(/\n/g, "<br>") + "</p>";
  document.getElementById("chat-messages").appendChild(el);
}

function bindInput() {
  const input = document.getElementById("player-input");
  const btn = document.getElementById("btn-send");

  async function send() {
    const content = input.value.trim();
    if (!content) return;

    btn.disabled = true;
    input.disabled = true;
    appendMessage({ role: "user", content: content });
    input.value = "";

    const loadingId = showTypingIndicator();

    try {
      const url = "/api/game/" + characterId + "/act";
      const res = await apiFetch(url, {
        method: "POST",
        body: JSON.stringify({ content: content })
      });

      removeTypingIndicator(loadingId);
      if (!res) return;

      appendMessage({ role: "assistant", content: res.data.narrative });
      renderCharPanel(res.data.character);
    } catch (e) {
      removeTypingIndicator(loadingId);
      showToast("天道暂时无法回应，请重试");
    } finally {
      btn.disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  btn.addEventListener("click", send);
  input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });
}
```

---

## 五、角色面板（古风卷轴样式）

```javascript
function renderCharPanel(character) {
  const info = character.infomation;
  const panel = document.getElementById("char-panel");
  panel.innerHTML = 
    <div class="scroll-frame">
      <h3 class="scroll-title">{info.realm.split("，")[0] || character.name}</h3>
      <div class="scroll-section">
        <span class="label">境界</span>
        <p>{info.realm}</p>
      </div>
      <div class="scroll-section">
        <span class="label">战力</span>
        <p>{info.power}</p>
      </div>
      <div class="scroll-section">
        <span class="label">位置</span>
        <p>{info.location}</p>
      </div>
      <div class="scroll-section">
        <span class="label">道心</span>
        <p>{info.dao_heart}</p>
      </div>
      <div class="scroll-section">
        <span class="label">物品</span>
        <p>{info.inventory}</p>
      </div>
    </div>;
}
```

---

## 六、弹窗系统

### 6.1 弹窗管理（modals/index.js）

```javascript
let currentModal = null;

export function initModals() {
  document.getElementById("modal-overlay").addEventListener("click", function(e) {
    if (e.target === e.currentTarget) closeModal();
  });
}

export function showModal(html) {
  document.getElementById("modal-container").innerHTML = html;
  document.getElementById("modal-overlay").classList.remove("hidden");
}

export function closeModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
  document.getElementById("modal-container").innerHTML = "";
}
```

### 6.2 登录/注册弹窗（modals/login.js）

```javascript
import { showModal, closeModal } from "./index.js";
import { apiFetch } from "../api.js";
import { setToken } from "../auth.js";
import { showCharListModal } from "./char-list.js";

export function showLoginModal() {
  showModal('
    <h2>踏入仙途</h2>
    <form id="login-form">
      <input name="username" placeholder="道号" required>
      <input name="password" type="password" placeholder="密令" required>
      <button type="submit" class="btn">登入</button>
    </form>
    <p class="switch-link">尚无道号？<a id="switch-register">开辟仙途</a></p>
  ');

  document.getElementById("login-form").addEventListener("submit", async function(e) {
    e.preventDefault();
    const form = new FormData(e.target);
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password")
      })
    });
    if (!res) return;
    setToken(res.data.token);
    closeModal();
    showCharListModal();
  });
}
```

---

*07-frontend.md v1.0 完成。下一步：[08-deployment.md](./08-deployment.md)。*


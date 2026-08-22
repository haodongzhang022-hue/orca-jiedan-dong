# 智能测评 App · 首页 + 登录页 UI（v2 · 粉红顶部横条 + 暖色界面）

> 交付编号：20260822 | 品类：App 前端 UI | 依据：用户新上传设计稿
> 规格：移动端优先 · 响应式 · 编码 UTF-8
> 两种形式：**① 纯前端 HTML 网页**（双击预览） + **② UniApp+Vue3 工程骨架**（可直接跑起来）

---

## 📁 目录结构

```
20260822_智能测评App_首页+登录页_v2/
├── README.md            # 本交付说明
├── html/                # ① 纯前端 HTML 网页（双击即可预览）
│   ├── index.html       #   1️⃣ 首页模块
│   ├── login.html       #   2️⃣ 登录页面
│   ├── style.css        #   共享样式（粉红顶部横条 + 暖色界面）
│   └── script.js        #   前端交互（表单校验 / 密码切换 / Tab 切换 / 跳转）
└── uniapp/              # ② UniApp + Vue3 工程骨架
    ├── package.json     #   依赖与脚本（dev:h5 / build:h5 等）
    ├── vite.config.js   #   Vite 配置（uni 插件）
    ├── index.html       #   H5 入口
    └── src/
        ├── main.js      #   Vue3 入口
        ├── App.vue      #   应用根组件 + 全局样式
        ├── pages.json   #   路由配置（pages/index、pages/login）
        ├── manifest.json#   应用配置
        ├── uni.scss     #   scss 主题变量（粉红 + 暖色）
        ├── static/      #   静态资源（tabbar 图标等）
        └── pages/
            ├── index/index.vue   # 1️⃣ 首页
            └── login/login.vue   # 2️⃣ 登录页
```

---

## ① 纯前端 HTML 网页

**打开方式**：双击 `html/index.html` 即可在浏览器预览，无外部依赖。

| 文件 | 说明 |
|---|---|
| `index.html` | 1️⃣ 首页模块（粉红顶部横条 + 暖色卡片） |
| `login.html` | 2️⃣ 登录页面（登录/注册 Tab 切换） |
| `style.css` | 共享样式 |
| `script.js` | 交互逻辑 |

---

## ② UniApp + Vue3 工程骨架

**运行方式**（在 `uniapp/` 目录下）：

```bash
# 安装依赖
npm install

# 运行到 H5（浏览器）
npm run dev:h5

# 构建 H5
npm run build:h5

# 运行到微信小程序
npm run dev:mp-weixin

# 用 HBuilderX 打开项目可直接运行到手机 / 模拟器
```

**路由配置**（`src/pages.json`）：

| 页面 | 路径 | 说明 |
|---|---|---|
| 首页 | `pages/index/index` | 1️⃣ 首页模块 |
| 登录页 | `pages/login/login` | 2️⃣ 登录页面 |

> 登录页支持通过参数进入注册 Tab：`/pages/login/login?tab=register`

---

## 🎨 设计风格（依据新设计稿）

- **粉红顶部横条**：渐变粉色横幅（`#f56e9c → #f78cab → #ffb86c`），暖色过渡
- **暖色界面**：暖粉渐变背景 + 蜜桃色光晕 + 粉色卡片
- **UI 组件**：圆角卡片、柔和阴影、线性/emoji 图标
- **整体**：温暖、亲和、现代，主色粉红 `#f56e9c`

## 功能清单

### 1️⃣ 首页模块
- 顶部 slogan「✨ AI 让学习更高效」
- App 简介：AI 测评题 / 知识巩固 / 成绩分析 / 错题本（四卡片）
- 核心按钮「开始测评」→ 引导登录
- 底部轻量登录 / 注册向导
- 底部导航：首页 / 测评 / 成绩 / 我的

### 2️⃣ 登录页面
- 登录方式：手机号 + 密码
- 表单校验：手机号格式（11 位大陆号码）、密码明文/隐藏切换、错误/成功提示
- Tab 切换：登录 / 注册 双表单
- 跳转入口：「立即注册」切换 Tab
- 返回按钮：回到 App 首页

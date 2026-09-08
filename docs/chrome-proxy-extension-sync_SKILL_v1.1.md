---
name: chrome-proxy-extension-sync
title: Chrome代理双浏览器插件互导与免费兜底技能
summary: 香港代理Chrome(ProxyProfile)与原版Chrome插件互导三方案；服务器停费0元兜底（Cloudflare Workers）；ChatGPT封香港IP说明；Obsidian插件选择。绑定五步法§二十二/全域模板#333/#337/项目脚手架。
version: v1.1
distilled_by: 汤小龙（汤哥AI分身）
distilled_at: 2026-09-08
triggers: [插件互导, 插件同步, 代理Chrome, ProxyProfile, 停费兜底, 免费代理, Cloudflare Workers, ChatGPT打不开, 90块钱服务器, 扩展同步, 书签同步, Web Clipper]
cost_mode: strict
---

# Chrome 代理双浏览器插件互导与免费兜底技能

> **一句话**：两个 Chrome 的插件**能互导**（Google 账号同步=双向全自动；企业策略=免点击强制装）；**不交服务器钱也有 0 元兜底**（Cloudflare Workers 免费代理）；ChatGPT 打不开是 OpenAI 封香港机房 IP，不是隧道坏了。

---

## 一、背景架构（本机现状）

```
原版 Chrome（默认 profile）          代理 Chrome（ProxyProfile 独立档案）
├─ 插件齐全（旧）                    ├─ 干净（新）
├─ 直连（被墙站打不开）               ├─ --proxy-server=socks5://127.0.0.1:1081
│                                   └─ 香港隧道 → Google/GitHub/WebStore 全通
        └──────── 同一台机器，profile 互相独立，插件不互通（除非同步）─────────
```

**关键认知**：Chrome 插件按 profile 存储。`--user-data-dir` 建了独立档案，所以新版"缺插件"是正常现象，不是坏了。

---

## 二、插件互导三方案（按推荐排序）

### 方案A：Google 账号同步（推荐 · 双向全自动）⭐
1. 代理 Chrome 打开 `chrome.com/settings`（或地址栏输 `chrome://settings/syncSetup`）
2. 登录**同一个 Google 账号**（就是你原版 Chrome 用的那个）
3. 开启同步 → 勾选「扩展程序」
4. **几分钟内旧插件全部自动出现**；以后任何一端装/删插件，另一端自动跟（双向）
- 优点：一次登录，永久双向同步，换电脑也生效
- 前提：登录 Google 需走代理（代理 Chrome 天然满足）

### 方案B：企业策略强制安装（免点击 · 我已内置一条）
- 已写 HKCU 注册表策略：`Software\Policies\Google\Chrome\ExtensionInstallForcelist`
- 策略对**本机所有 Chrome profile 都生效**（原版+代理版一起装）→ 这就是"相互导"的系统级答案
- 添加新插件：值名递增（"2"、"3"...），值为 `扩展ID;https://clients2.google.com/service/update2/crx`
- 扩展ID 查看：`chrome://extensions` → 开发者模式 → 每个插件卡片上有 ID
- 移除：删对应注册表值

### 方案C：开发者模式手动加载（应急 · 不走商店）
1. 原版 Chrome 打开 `chrome://extensions` → 开发者模式 → 找到插件「ID」
2. 文件位置：`C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Extensions\<扩展ID>\<版本号>\`
3. 把整个版本号文件夹拷出来 → 代理 Chrome `chrome://extensions` → 开发者模式 →「加载已解压的扩展程序」
- 缺点：不会自动更新；适合个别商店装不了的插件

> **三方案可叠加**：账号同步为主，策略兜底，手动加载应急。

---

## 三、停费兜底（90多块钱不交了怎么办）

### 3.1 先澄清影响面
不续费 → 腾讯云释放服务器 → SSH 隧道断 → **Google/GitHub/WebStore 又被墙**（回到解放前）。但：
- **GitHub 影响小**：国内有直连加速镜像（如 `ghproxy` 类前缀），git clone/下载通常可用
- **Google 系必须代理**：需要 0 元替代

### 3.2 0 元兜底方案：Cloudflare Workers（推荐）
- **成本**：0 元（免费版每天 10 万请求，个人用绰绰有余）
- **原理**：Cloudflare 边缘节点做中转（VLESS+WS+TLS），不需要任何自己的服务器
- **部署**（一次性 10 分钟）：
  1. 免费注册 Cloudflare 账号 → 创建 Worker
  2. 部署开源 edgetunnel 类脚本（GitHub 搜 `edgetunnel`，复制 worker.js 粘贴）
  3. 生成 vless 配置链接 → 客户端导入（或转 HTTP/SOCKS 给 Chrome）
- **注意**：CF 免费域名 `workers.dev` 在国内时好时坏，最好绑一个自己的域名（域名年费约几十元，也可用免费二级域名）
- **能力圈评估**：90元/月服务器还有资料抓取/CI 等生产力用途，若只为上网则 CF 免费方案性价比完胜

### 3.3 决策表

| 场景 | 方案 | 成本 |
|------|------|------|
| 服务器在续费 | SSH 隧道（现方案） | ¥90/月（含生产力用途） |
| 只为上网 | Cloudflare Workers | 0 元 |
| 只用 GitHub | ghproxy 直连加速 | 0 元 |

---

## 四、两个高频疑问解答

### 4.1 ChatGPT 显示 "Unable to load site [IP:43.161.202.206]"？
**OpenAI 屏蔽了香港腾讯云机房 IP**（它检测到数据中心 IP 主动拒绝，跟"VPN 请关闭"一个意思）。不是隧道坏了。换出口 IP 或直连（ChatGPT 国内也无法直连，故此站暂时无解，与 Codex 无关——Codex 走的是自建网关所以能用）。

### 4.2 Web Store 搜 Obsidian 选哪个？
**选第一个「Obsidian Web Clipper」**（obsidian.md 官方出品、4.8★、精选标记）。已通过企业策略自动安装，无需手动。

---

## 五、回滚 / 恢复速查

| 场景 | 动作 |
|------|------|
| 隧道半死 | `hk_proxy_guard.bat` 60秒自愈 |
| 服务器 Xray 改坏 | `cp config.json.bak config.json && systemctl restart xray` |
| 插件策略想撤销 | 删 `HKCU\Software\Policies\Google\Chrome\ExtensionInstallForcelist` 下对应值 |
| 账号同步想断开 | 代理 Chrome 设置 → 关闭同步 |

---

## 六、三载体绑定

- **五步法**：§二十二 成本底线（兜底方案 0 元优先）+ 置顶「知识库先查铁律」（2026-09-08）
- **全域模板**：#333（Chrome代理插件互导与免费兜底）+ #337（知识库先查后沉淀协议）
- **项目脚手架**：注册技能名 `chrome-proxy-extension-sync`，触发词见 frontmatter
- **Obsidian 归档**：`我的AI分身/Obsidian知识库/01-AI工具资源/20260903_香港服务器代理隧道打通与自愈守护手册.md` 第十节
- **乐享知识库**：同步上传「汤嘉锋的个人知识库」

## 七、2026-09-08 实证补遗（书签同步 + Web Clipper 修复）

**本机四台浏览器实况（先盘点再动手）**：
| 浏览器 | 数据目录 | 登录 | 书签 | Web Clipper |
|---|---|---|---|---|
| GptBrowser（带AI标识） | `D:\Chrome\UserData\Default` | ✅ 账号 | 1018条（权威源） | ✅ 1.7.1 |
| Chrome 原版 | `...\Google\Chrome\User Data\Default` | ✅ 同账号 | 1018条 | ✅ 1.7.1 |
| ProxyProfile（香港代理） | `...\Google\Chrome\ProxyProfile` | ❌ 未登录 | 无（已文件对齐1018条） | ✅ 1.7.1 |
| SPChrome（带AI标识·截图那台） | `...\Local\SPChrome\User Data\Default` | ❌ | **加密存储非JSON** | 空目录→已补文件 |

**坑与修法（全部实证）**：
1. **策略 ID 笔误**：企业策略里 `cnjifjpddelmedmihgijeibhnjdogjmm` 是错的，Web Clipper 真实商店 ID = **`cnjifjpddelmedmihgijeibhnjfabmlf`**（4 台浏览器 manifest 实证）。读法：Python `winreg` 枚举 `HKCU\Software\Policies\Google\Chrome\ExtensionInstallForcelist`
2. **SPChrome「扩展栏没有某插件」先查目录**：`Extensions\<ID>\` 若为空目录=下载失败残留；从别的浏览器拷完整版本文件夹过去，若 `Secure Preferences` 里注册还在（state=1 启用）→ **重启浏览器即自动恢复**，无需 RPA/重装
3. **ProxyProfile 书签文件级对齐法**（账号同步的前置替代）：①只杀命令行含 ProxyProfile 的 chrome 进程（别全杀）②拷权威源 `Bookmarks` → `ProxyProfile\Default\`，**删顶层 `checksum` 键**（Chrome 首启重算）③重启即见全部书签
4. **账号级持续同步的唯一手动步骤**：ProxyProfile 首次登录 Google 账号（密码/2FA 程序无法代办）→ `chrome://settings/syncSetup` 开同步。登录前文件对齐已保证书签一致
5. **SPChrome 书签是加密存储**（Bookmarks 文件头非 JSON，2.5MB 密文）→ fork 魔改，无法文件级对齐，只能靠商店/账号方案
6. **一键对齐脚本**：`G:\tmp\align_browsers_0908.py`（关实例→书签对齐→补扩展文件→注册检查，可复用）

---

*v1.0 · 汤小龙蒸馏 · 万法皆空，因果不空*

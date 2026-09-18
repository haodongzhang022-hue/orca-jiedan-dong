# Cloud Studio T4 · ComfyUI + Wan2.2 漫剧部署手册

> **任务卡**：CloudStudio-T4-ComfyUI-Wan2.2漫剧部署手册 v1.0
> **时间**：2026-09-16 · 执行人：**汤小龙（AI 分身）**
> **方法**：龙虾五步法 V3.6 + 1234 四化迭代 · 全域模板
> **数据来源**：本机 PowerShell 实测 + hf-mirror / GitHub API 实时探针 + ComfyUI 官方工作流模板原文

---

## 〇、先说结论

| 问题 | 结论 |
|---|---|
| 能不能部署到 Cloud Studio T4？ | **能。** 路径完全可行 |
| 你给的那份脚本能直接跑吗？ | **不能。有 5 处会直接跑挂**（下方逐条给证据） |
| 20 机时够不够跑漫剧小样？ | **够，但没你想的那么多** —— 见第五章预算表，先跑「小样档」 |
| 你说「10 秒视频约 3 分钟/条」准确吗？ | **不准确，这是 T4 上最容易烧光额度的误判**，见第五章 |

---

## 一、你的脚本 5 处必修（全部有实测证据）

### ❌ 错误 1：Wan2.2 的 ComfyUI 插件仓库不存在

你写的：
```bash
git clone https://github.com/Wan-Video/Wan2.2-ComfyUI custom_nodes/Wan2.2-ComfyUI
```
**实测**：`https://api.github.com/repos/Wan-Video/Wan2.2-ComfyUI` → **HTTP 404**，仓库不存在。

**真相**：ComfyUI 已**原生内置** Wan2.2 支持（`comfy-core` 自带 `Wan22ImageToVideoLatent` 等节点，模板标注 `ver: 0.3.45`），**不需要任何第三方 Wan 插件**。多装反而引入冲突。

### ❌ 错误 2：模型仓名不存在，权重会下载失败

你写的：
```python
huggingface_hub.snapshot_download('Wan-Video/Wan2.2-5B', local_dir='models/wan2.2')
```
**实测**：`Wan-Video/Wan2.2-5B` 仓不存在。

**正确的仓（官方模板里写死的）**：

| 文件 | 大小（实测） | 落位目录 | 来源仓 |
|---|---|---|---|
| `wan2.2_ti2v_5B_fp16.safetensors` | **9.31 GB** | `models/diffusion_models/` | `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` |
| `wan2.2_vae.safetensors` | **1.31 GB** | `models/vae/` | `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | **6.27 GB** | `models/text_encoders/` | `Comfy-Org/**Wan_2.1**_ComfyUI_repackaged` ← 注意是 2.1 仓 |

**合计 16.89 GB**，不是你说的「约 9.8G」。9.8G 只是主模型那一个文件。

### ❌ 错误 3：HuggingFace 直连在国内不通（这条最致命）

本机实测（禁用代理、直连）：
```
https://huggingface.co/api/models/Comfy-Org/Wan_2.2_ComfyUI_Repackaged
→ URLError: WinError 10060 连接超时
https://hf-mirror.com/api/models/Comfy-Org/Wan_2.2_ComfyUI_Repackaged
→ HTTP 200 ✅
```

你的脚本直接 `snapshot_download` 会**卡在 0% 无限转圈**，而实例在**持续扣机时**。这是最烧钱的一种失败。

**修法**：`export HF_ENDPOINT=https://hf-mirror.com`（已写进修正脚本）。

### ❌ 错误 4：工作流 JSON 是伪格式，ComfyUI 导不进去

你给的 JSON 缺 `last_node_id` / `size` / `inputs` / `outputs` / `properties` 等必要字段，且节点名是编的：
- `Wan2.2ImageToVideo` → 真实是 **`Wan22ImageToVideoLatent`**（22 无点、Latent 结尾）
- `CheckpointLoaderSimple` + `ckpt: sdxl-base` → Wan2.2 5B **不是 checkpoint 结构**，是「独立 diffusion model + 独立 VAE + 独立 text encoder」，用 `UNETLoader` / `VAELoader` / `CLIPLoader` 三个分开加载
- **少了 `ModelSamplingSD3`（shift=8）** —— 这个节点不在，即使勉强跑起来画质会崩

**已修**：我直接抓了 ComfyUI 官方模板原文 `video_wan2_2_5B_ti2v.json`（14,175 字节，HTTP 200），基于它生成了 **3 个可直接 Load 的真实工作流**（见第四章）。

### ❌ 错误 5：默认分辨率会让第一条片子就跑爆显存

官方模板默认 **1280×704 / 121 帧**，这是给 A100/H100 级别（24GB+）准备的。T4 只有 16GB，而三个模型权重加起来 **16.89GB 已经超过显存**，必须靠 offload 到内存硬撑。

跑默认参数在 T4 上的后果：极慢，甚至 OOM 直接失败 —— **而失败也一样扣机时**。

**已修**：生成的工作流已降到 **480×832 / 49 帧**（T4 友好档）。

---

## 二、T4 的三条硬限制（决定了为什么必须降配）

T4 是 **Turing 架构（SM 7.5）**，不是新卡。三条硬限制：

| 限制 | 后果 | 应对 |
|---|---|---|
| **不支持 bf16**（需 Ampere SM80+） | 只能用 fp16 权重 | 方案已选 `fp16` 版主模型 ✅ |
| **不支持原生 fp8**（需 Ada/Hopper） | `umt5_xxl_fp8` 文本编码器会走软件反量化，比硬件 fp8 慢 | 可接受；若嫌慢可换 `umt5_xxl_fp16`（11.37GB，但更吃显存） |
| **不支持 FlashAttention 2**（需 Ampere+） | 注意力走朴素实现，显存与速度都吃亏 | 别装 flash-attn，装了也编译不过 |

另外：**16GB 显存装不下 16.89GB 权重** → ComfyUI 会自动把一部分权重放内存。T4 实例配 32GB 内存，够用，但这是速度慢的主因。

---

## 三、修正版一键部署脚本

已落盘：**`docs/CloudStudio_T4_Wan2.2_一键部署.sh`**

在 Cloud Studio 网页终端里**全选粘贴 → 回车**即可。核心修正点：

| # | 原脚本 | 修正后 |
|---|---|---|
| 1 | 无镜像设置 | `export HF_ENDPOINT=https://hf-mirror.com` |
| 2 | 无 pip 镜像 | 阿里云 PyPI 镜像 |
| 3 | `git clone` 官方 Wan 插件（404） | **删除**，ComfyUI 原生支持 |
| 4 | `snapshot_download('Wan-Video/Wan2.2-5B')` | 三个文件分别从**正确的官方仓**拉取 + 自动搬到正确目录 |
| 5 | 无断点 | 检测已存在且 >100MB 则跳过（重启实例不重下） |
| 6 | 无磁盘检查 | 开头 `df -h` 提示需 ≥25GB |
| 7 | 无环境自检 | 打印 torch 版本 / CUDA 可用性 / 算力等级 |

脚本自带 **模型落位自检**，跑完会打印三行 `OK/MISS`。

---

## 四、工作流（已生成 3 套，可直接 Load）

已落盘到 `docs/`：

| 文件 | 分辨率 | 时长 | 用途 |
|---|---|---|---|
| `wan22_5b_ti2v_480x832_49f_竖屏小样.json` | 480×832×49 | 约 2.0s | **先跑这个** 验证链路 |
| `wan22_5b_ti2v_480x832_81f_竖屏标准.json` | 480×832×81 | 约 3.4s | 正式分镜 |
| `wan22_5b_ti2v_832x480_49f_横屏小样.json` | 832×480×49 | 约 2.0s | 横屏物料 |

**相对官方模板的改动**（全部为必要修正）：

1. 分辨率/帧数 → T4 友好档
2. `LoadImage` 的 `mode` 从 `4`(bypass) 改为 `0`(启用) → **开箱即是「图生视频」**，不用再按 Ctrl+B
3. 正/负向提示词 → 换成你的漫剧提示词
4. `properties.models` 里的下载 URL → **改写为 `hf-mirror.com`**（这样在 ComfyUI 界面里点"下载模型"按钮，走的是能通的镜像）
5. `SaveVideo` 输出前缀 → `manju`

**导入方式**：ComfyUI 界面 → 把 JSON 文件拖进画布（或菜单 Load）→ 选分镜图 → Queue。

**生成的三个 JSON 已通过自检**：
```
no_bogus_node            : true   (无 Wan2.2ImageToVideo / CheckpointLoaderSimple 等假节点)
has_ModelSamplingSD3     : true   (shift=8 在)
has_Wan22ImageToVideoLatent: true
has_SaveVideo            : true
loadimage_enabled        : [0]    (i2v 已启用)
url_is_mirror            : true
```

---

## 五、20 机时怎么花（这是最关键的判断）

### 5.1 先纠正你的预期

你说「10 秒 Wan2.2 视频约 3 分钟/条」—— 这个数字**大概率来自更强的卡**。折算一下：

- 10 秒 @ 24fps = **240 帧**，是官方默认 121 帧的近 2 倍
- T4 fp16 算力 ≈ 65 TFLOPS，且 fp8 走软件反量化、注意力无 FlashAttention 加速
- 16.89GB 权重 > 16GB 显存 → 全程在 offload，速度再打折扣

**诚实的估算区间**（**首次实跑后必须回填实测值**，别拿估算当结论）：

| 档位 | 分辨率×帧数 | 单条预估耗时 | 20 机时（=16.7h T4）能出 |
|---|---|---|---|
| 小样 | 480×832×49 | 约 4~10 分钟 | **约 100~250 条** |
| 标准 | 480×832×81 | 约 8~16 分钟 | 约 60~125 条 |
| 官方默认 | 1280×704×121 | 约 25~60 分钟 | 约 17~40 条 |
| 你说的 | 1280×704×**240** | 约 50~120 分钟 | **约 8~20 条** |

> 结论：**20 机时够跑完整部漫剧的分镜小样（60~120 个镜头）**，前提是走「小样/标准」档，不是 10 秒满帧档。

### 5.2 额度优先级（按你说的执行）

| 额度 | 数量 | 到期 | 用法 |
|---|---|---|---|
| **绑定赠送（长期）** | **20 机时** | 2027-09-16 | ✅ **优先用这个** |
| 每日签到（短期） | 2 机时 | 剩余 6 天 | 留作应急 |
| 每日活跃 | +2 机时/天 | 短期 | 顺手 |

截图确认：当前 **已用 0/22 机时（0%）**，干净启动。

### 5.3 三条省钱铁律

1. **跑第一条就计时** —— 拿手机秒表掐一次，回填到预估值，再决定批量规模。**别凭估算一把梭。**
2. **模型只下一次** —— 16.89GB 下载完成后，重启实例不用重下（脚本有跳过逻辑）。但如果**删了实例**就要重下，注意别乱删。
3. **跑完立刻停机** —— 官方明确：资源包耗尽后**不会自动停机**，会自动转按量付费扣余额；IDE 页面挂着（哪怕最小化）照样扣。

---

## 六、完整操作步骤（4 步）

### 步骤 1：新建 T4 实例
Cloud Studio 首页 → **新建工作空间** → 选 **GPU T4 16G** 规格 → 启动 → 进入网页终端。
> 参考你的截图：`cloudstudio.net/settings/data-resource` 那个页面是**额度页**，建实例要去**工作空间/应用**页。

### 步骤 2：跑部署脚本
把 `docs/CloudStudio_T4_Wan2.2_一键部署.sh` 的**全部内容**粘进终端，回车。
预计耗时：依赖安装 3~6 分钟 + 模型下载 16.89GB（镜像速度决定，可能 10~40 分钟）。
> **下载阶段也在扣机时**，这是必要成本，一次性的。

### 步骤 3：验证节点
另开一个终端标签（或先 Ctrl+C 停掉 ComfyUI）跑：
```bash
python check_wan_nodes.py
```
全部 `[ OK ]` 才继续。

### 步骤 4：导入工作流出片
重启 ComfyUI → 侧边栏点 **8188** 预览进界面 → 拖入 `wan22_5b_ti2v_480x832_49f_竖屏小样.json` → 上传一张本机出的分镜图到 `input/` → Queue → **掐表记时间**。

---

## 七、批量出片（可选，链路跑通后再用）

已落盘：**`docs/batch_manju_i2v.py`**

```bash
python batch_manju_i2v.py --dry-run    # 先看预算，不提交
python batch_manju_i2v.py              # 真跑
```
改文件里的 `SHOTS` 列表（图片名 + 提示词 + 档位）即可。有 `--dry-run` 预算闸门，避免误烧额度。

**注意**：该脚本用 API 格式提交，节点参数名基于官方模板推导。**必须先跑通一次 GUI 出片再用它** —— `check_wan_nodes.py` 已帮你验证参数名。

---

## 八、风控红线

| # | 红线 | 原因 |
|---|---|---|
| 1 | **跑完立刻「应用管理 → 停止使用」** | 资源包耗尽不自动停机，会扣余额；光关浏览器要等约 10 分钟 |
| 2 | **不要删实例** | 删了 16.89GB 模型要重下，又烧一次机时 |
| 3 | **第一条必须掐表** | 估算值不可信，实测值才可用来规划批量 |
| 4 | **客户人像素材谨慎投喂公共实例** | 免费实例的数据政策需自行评估 |
| 5 | **别装 flash-attn / xformers 强开** | T4 不支持，编译失败浪费时间与机时 |
| 6 | **账单延迟约 2 小时** | 别被"已停机还收到提醒"吓到，以真实用时为准 |

---

## 九、诚实交代：哪些我没做、做不到

| 事项 | 状态 |
|---|---|
| 修正你的脚本 | ✅ 已做，5 处错误全部修掉 |
| 拿到官方真实工作流 | ✅ 已做，HTTP 200，14,175 字节原始文件 |
| 生成 T4 友好工作流 | ✅ 3 套，已通过程序自检 |
| **登录你的 Cloud Studio 建实例** | ❌ **做不到** —— 需要你的浏览器登录态，本机当前无可用调试端口（实测 9222/9223/9224/9225/9333 全部未监听）。这一步必须你点。 |
| **在云端实跑第一条视频** | ❌ 未做（依赖上一步） |
| 单条真实耗时 | ⏳ 待你跑完第一条后回填 |

---

## 十、下一步

1. 你建 T4 实例 → 粘脚本 → 跑第一条 → **把耗时告诉我**，我回填预算表并校准 `EST_MIN_PER_SHOT`
2. 链路跑通后，把本机 CPU 出的分镜图批量喂进 `batch_manju_i2v.py`
3. 回填后更新本手册至 v1.1，并同步 `comfyui-manju-zero-cost` 技能

---

## 附：实测证据索引（全部可复核）

| 探针对象 | 结果 |
|---|---|
| `api.github.com/repos/Wan-Video/Wan2.2-ComfyUI` | **404**（不存在的仓库） |
| `api.github.com/repos/comfyanonymous/ComfyUI` | 200，已迁移至 `Comfy-Org/ComfyUI`，133,343 stars，2026-09-15 仍在更新 |
| `api.github.com/repos/Kosinkadink/ComfyUI-VideoHelperSuite` | 200，1,841 stars |
| `raw.githubusercontent.com/.../video_wan2_2_5B_ti2v.json` | 200，14,175 字节（**已保存**） |
| `huggingface.co`（直连） | **WinError 10060 超时** |
| `hf-mirror.com` | **200** ✅ |
| `wan2.2_ti2v_5B_fp16.safetensors` | 9,999,658,848 B = **9.31 GB** |
| `wan2.2_vae.safetensors` | 1,409,400,960 B = **1.31 GB** |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6,735,906,897 B = **6.27 GB** |
| `raw.githubusercontent.com`（本机直连） | WinError 10054 强制关闭 → 需走 `gh-proxy.com`（实测 200） |
| Cloud Studio 计费文档 | 200 |
| 本机 CDP 端口 9222/9223/9224/9225/9333 | 全部未监听（无法接管浏览器） |

# ORCA项目磁盘分层存储方案文档

> 版本：v1.0 | 生成时间：2026-08-03 | 龙虾五步法Step3输出
> 适用范围：所有ORCA项目（数字人视频、meme代币、开源工具等）

## 一、架构总览

### 1.1 核心设计原则
- **E盘（核心程序层）**：存放源代码、程序工程、脚本、配置文件、轻量文档
- **G盘（大容量数据层）**：统一承载大体积数据、模型权重、数据集、生成素材、缓存数据库
- **目录联结（Junction）**：使用Windows `mklink /J` 实现透明映射，代码无需改动、程序无感

### 1.2 优势
1. **零代码修改**：程序访问路径完全不变，规避大量代码改动引发的报错
2. **磁盘空间优化**：E盘仅保留轻量代码，大容量数据统一存放在G盘
3. **维护简便**：所有大文件集中管理，便于备份、清理和迁移
4. **性能提升**：G盘通常有更大空间和更好的I/O性能

## 二、现状评估分析

### 2.1 磁盘空间现状
| 磁盘 | 总容量 | 已用 | 可用 | 使用率 | 状态 |
|------|--------|------|------|--------|------|
| E盘 | 141G | 123G | 18G | 88% | ⚠️ 紧张 |
| G盘 | 932G | 674G | 259G | 73% | ✅ 充足 |
| C盘 | 155G | 147G | 8.4G | 95% | ⚠️ 紧张 |

### 2.2 项目文件评估

#### 任务A：双人数字人项目
**目录结构**：
```
企业微信群定制接单项目/
├── 数字人视频订单/          # 订单管理
├── tools/wav2lip/           # Wav2Lip代码库（2.8M）
│   ├── checkpoints/         # 模型权重目录（当前为空）
│   └── ...
├── 调研报告_*.md            # 调研文档
└── 交付文档_*.md            # 交付文档
```

**大容量对象识别**：
1. **Wav2Lip模型权重**（待下载）
   - Wav2Lip: ~100MB（高精度口型同步）
   - Wav2Lip+GAN: ~200MB（更好的视觉质量）
   - 人脸检测模型: ~100MB（s3fd.pth）
   - **总计**: ~400MB

2. **SadTalker模型权重**（待部署）
   - 模型大小: ~1GB-6GB（根据配置）
   - 状态: 调研报告中提到，尚未下载

3. **音频素材**（待生成）
   - 测试音频文件
   - 背景音乐
   - **预估**: 100MB-1GB

4. **视频素材**（待生成）
   - 输入视频/图片
   - 输出视频
   - **预估**: 1GB-10GB（根据订单量）

5. **推理缓存**（运行时生成）
   - 临时文件
   - **预估**: 500MB-2GB

**文件分类**：
- **长期持续复用文件**：模型权重、核心脚本
- **仅当前测试阶段临时文件**：测试视频、临时缓存

#### 任务B：meme代币部署项目
**评估结果**：
- 合约脚本、文档属于轻量代码
- 无大型资源（模型、素材、数据库）
- **结论**：暂不需要跨盘迁移，保留在E盘即可

### 2.3 待引入开源项目评估（12个GitHub开源工具）

#### ✅ 轻量框架（源码保留E盘）：
1. LibreChat - 聊天界面
2. n8n - 工作流自动化
3. agent-skills - Agent技能框架
4. 其他轻量工具...

#### ⚠️ 携带大模型权重项目（资源必须存放G盘）：
1. **VoxCPM** - 语音合成模型
   - 模型权重: ~2GB-5GB
   - 素材库: ~1GB
   - **必须存放G盘**

2. **HyperFrames** - 视频处理框架
   - 模型权重: ~1GB-3GB
   - 视频素材: ~5GB-10GB
   - **必须存放G盘**

3. **MoneyPrinterTurbo** - 视频生成工具
   - 模型权重: ~2GB-4GB
   - 生成素材: ~10GB+
   - **必须存放G盘**

4. 其他携带大模型的项目...

## 三、目录规范设计

### 3.1 固定顶层路径

#### E盘（工程入口）
```
E:\龙虾AI主控中心\我的AI分身\orca\
├── 企业微信群定制接单项目\    # 当前项目
├── 其他ORCA项目\              # 未来项目
└── ...
```
**规则**：维持现有工程目录结构不动

#### G盘（数据仓库）
```
G:\orca_data_pool\
├── model_weights\            # 所有AI预训练模型权重
│   ├── wav2lip\              # Wav2Lip模型
│   ├── sadtalker\            # SadTalker模型
│   ├── voxcpm\               # VoxCPM模型
│   └── ...
├── media_assets\             # 音视频素材、输入图片、成片输出
│   ├── input\                # 输入素材
│   ├── output\               # 输出成品
│   └── background\           # 背景素材
├── dataset_cache\            # 数据集、huggingface本地缓存
├── database_storage\         # sqlite、向量数据库、持久化缓存
└── temp_render_output\       # 临时渲染产出
```

### 3.2 迁移规则

#### 规则1：已下载模型迁移
对于已经下载完成的Wav2Lip模型权重：
1. 迁移至 `G:\orca_data_pool\model_weights\wav2lip`
2. 在原E盘项目 `tools/wav2lip/checkpoints` 创建**目录联结**
3. 程序访问路径保持不变

#### 规则2：新下载模型
后续所有新下载模型、渲染生成视频，直接落地G盘数据池

#### 规则3：自动检测逻辑
脚本内新增自动检测逻辑：检测目标文件夹是否为软链接，防止重复下载两份模型

## 四、执行顺序约束

### 4.1 优先级
1. 先完成**现状分析报告**（本文档）
2. 等待当前Wav2Lip模型下载、首条测试视频生成流程跑完
3. 测试任务完成后，再执行模型文件跨盘迁移+建立软链接
4. 将这套【E盘代码+G盘数据池+目录联结】分层架构方案，沉淀进入全域模板、龙虾五步法标准规范

### 4.2 当前阶段
- **立即执行**：创建G盘数据池目录结构
- **延后执行**：模型文件迁移（等待测试完成）
- **长期执行**：架构方案沉淀

## 五、资源分级清单

### 5.1 立即部署资源
| 资源类型 | 大小 | 存放位置 | 状态 |
|----------|------|----------|------|
| Wav2Lip代码库 | 2.8M | E盘（保持原位） | ✅ 已就位 |
| G盘数据池目录结构 | - | G:\orca_data_pool | ✅ 已创建 |

### 5.2 二期部署资源（测试完成后）
| 资源类型 | 大小 | 存放位置 | 状态 |
|----------|------|----------|------|
| Wav2Lip模型权重 | ~400MB | G:\orca_data_pool\model_weights\wav2lip | ⏳ 待下载 |
| SadTalker模型权重 | ~1-6GB | G:\orca_data_pool\model_weights\sadtalker | ⏳ 待部署 |
| 测试视频素材 | ~100MB | G:\orca_data_pool\media_assets\input | ⏳ 待生成 |

### 5.3 三期部署资源（开源工具引入后）
| 资源类型 | 大小 | 存放位置 | 状态 |
|----------|------|----------|------|
| VoxCPM模型权重 | ~2-5GB | G:\orca_data_pool\model_weights\voxcpm | 📋 规划中 |
| HyperFrames模型 | ~1-3GB | G:\orca_data_pool\model_weights\hyperframes | 📋 规划中 |
| MoneyPrinterTurbo模型 | ~2-4GB | G:\orca_data_pool\model_weights\moneyprinter | 📋 规划中 |

### 5.4 仅归档不下载资源
| 资源类型 | 说明 |
|----------|------|
| 大型数据集 | 仅当实际需要时下载 |
| 通用预训练模型 | 优先使用轻量版本 |
| 历史版本模型 | 仅保留最新版本 |

## 六、软链接创建脚本

### 6.1 PowerShell一键脚本
```powershell
# ORCA项目磁盘分层存储 - 软链接创建脚本
# 版本：v1.0 | 生成时间：2026-08-03

# 配置变量
$G_DATA_POOL = "G:\orca_data_pool"
$E_PROJECT_ROOT = "E:\龙虾AI主控中心\我的AI分身\orca\企业微信群定制接单项目"

# 创建G盘数据池目录结构
Write-Host "创建G盘数据池目录结构..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\wav2lip"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\sadtalker"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\media_assets\input"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\media_assets\output"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\media_assets\background"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\dataset_cache"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\database_storage"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\temp_render_output"

# 创建软链接函数
function Create-JunctionLink {
    param(
        [string]$Source,
        [string]$Target
    )
    
    # 检查目标目录是否存在
    if (-not (Test-Path $Target)) {
        Write-Host "目标目录不存在: $Target" -ForegroundColor Red
        return
    }
    
    # 检查源路径是否已存在
    if (Test-Path $Source) {
        # 检查是否已经是软链接
        $item = Get-Item $Source
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Write-Host "软链接已存在: $Source -> $Target" -ForegroundColor Yellow
            return
        } else {
            Write-Host "源路径已存在且不是软链接: $Source" -ForegroundColor Red
            return
        }
    }
    
    # 创建软链接
    try {
        New-Item -ItemType Junction -Path $Source -Target $Target -Force
        Write-Host "创建软链接成功: $Source -> $Target" -ForegroundColor Green
    } catch {
        Write-Host "创建软链接失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 创建Wav2Lip模型权重软链接
Write-Host "创建Wav2Lip模型权重软链接..." -ForegroundColor Green
$wav2lipSource = "$E_PROJECT_ROOT\tools\wav2lip\checkpoints"
$wav2lipTarget = "$G_DATA_POOL\model_weights\wav2lip"

# 备份原有目录（如果存在且不是软链接）
if (Test-Path $wav2lipSource) {
    $item = Get-Item $wav2lipSource
    if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        $backupPath = "${wav2lipSource}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Rename-Item -Path $wav2lipSource -NewName $backupPath
        Write-Host "备份原有目录: $wav2lipSource -> $backupPath" -ForegroundColor Yellow
    }
}

Create-JunctionLink -Source $wav2lipSource -Target $wav2lipTarget

# 创建媒体素材软链接（示例）
Write-Host "创建媒体素材软链接..." -ForegroundColor Green
$mediaSource = "$E_PROJECT_ROOT\media_assets"
$mediaTarget = "$G_DATA_POOL\media_assets"
Create-JunctionLink -Source $mediaSource -Target $mediaTarget

Write-Host "软链接创建完成！" -ForegroundColor Green
Write-Host "请验证软链接是否正常工作：" -ForegroundColor Cyan
Write-Host "1. 检查目录是否可访问" -ForegroundColor Cyan
Write-Host "2. 测试程序是否能正常读写文件" -ForegroundColor Cyan
```

### 6.2 使用说明
1. 以管理员身份运行PowerShell
2. 执行脚本：`.\create_junction_links.ps1`
3. 验证软链接是否正常工作

## 七、验证清单

### 7.1 软链接验证
- [ ] G盘数据池目录结构已创建
- [ ] Wav2Lip checkpoints软链接已创建
- [ ] 媒体素材软链接已创建
- [ ] 程序可正常访问软链接路径

### 7.2 功能验证
- [ ] Wav2Lip推理测试通过
- [ ] 视频生成测试通过
- [ ] 文件读写测试通过

### 7.3 性能验证
- [ ] 软链接访问速度正常
- [ ] 无权限问题
- [ ] 无路径解析错误

## 八、风险与应对

### 8.1 潜在风险
1. **软链接失效**：G盘路径变更或删除
2. **权限问题**：跨盘访问权限不足
3. **性能影响**：跨盘I/O可能略慢

### 8.2 应对措施
1. **定期检查**：添加软链接健康检查脚本
2. **权限配置**：确保G盘目录Everyone可读
3. **性能监控**：监控I/O性能，必要时调整

## 九、后续优化

### 9.1 自动化脚本
1. 软链接健康检查脚本
2. 自动备份脚本
3. 磁盘空间监控脚本

### 9.2 架构扩展
1. 支持更多项目类型
2. 支持多级数据池
3. 支持云存储集成

## 十、沉淀到全域模板

### 10.1 全域模板协议
本方案应沉淀为全域模板协议，编号建议：#XXX

### 10.2 龙虾五步法集成
1. **Step1 意图识别**：识别项目是否需要大容量存储
2. **Step2 能力映射**：映射到G盘数据池架构
3. **Step3 方案规划**：制定具体迁移方案
4. **Step4 自主执行**：执行迁移和软链接创建
5. **Step5 反思进化**：优化架构和脚本

---

**文档生成**：Hermes Agent | 龙虾五步法Step3输出
**版本控制**：v1.0 | 2026-08-03
**适用范围**：所有ORCA项目
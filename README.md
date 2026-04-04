# TMD Controller

[![Version](https://img.shields.io/badge/version-7.0.0-blue.svg)](https://github.com/tmd-project)
[![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

Twitter Media Downloader 控制程序（TMD Controller / **tmdc**），提供交互式终端菜单（TUI）和完整的命令行接口（CLI），大幅简化 [TMD](https://github.com/tweetduck/TwitterMediaDownloader) 的使用流程。采用模块化架构设计，支持依赖注入、协议接口分层、双轨风控延迟、多账号轮询、增量时间戳同步等高级特性。

---

## 目录

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [功能特性](#功能特性)
- [环境依赖](#环境依赖)
- [安装](#安装)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
  - [交互式菜单](#交互式菜单)
  - [配置向导](#配置向导)
  - [高级选项](#高级选项)
  - [恢复下载](#恢复下载)
  - [固定列表](#固定列表)
  - [时间戳管理](#时间戳管理)
  - [Profile 下载](#profile-下载)
- [命令行模式](#命令行模式)
- [命令行参数详解](#命令行参数详解)
- [使用示例](#使用示例)
- [参数兼容性速查表](#参数兼容性速查表)
- [配置文件](#配置文件)
- [项目结构](#项目结构)
- [架构设计细节](#架构设计细节)
- [开发指南](#开发指南)
- [打包发布](#打包发布)
- [测试](#测试)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [许可证](#许可证)

---

## 项目概述

TMD Controller（简称 **tmdc**）是一个 Windows 专用的 Python 控制程序，为 Twitter Media Downloader（TMD）提供友好的操作界面和强大的自动化能力。

### 核心定位

TMD 本身是一个命令行工具，tmdc 在其之上构建了：

| 层次 | 职责 |
|------|------|
| **TMD（底层）** | 实际的媒体下载引擎，通过 `tmd.exe` 执行 |
| **tmdc（控制层）** | 用户交互、参数解析、任务调度、状态管理 |

### 设计哲学

- **两层分离**：业务逻辑（services/）与 UI 展示（menus/）完全解耦，所有服务不含任何 UI 输出
- **协议驱动**：通过 `Protocol` 接口定义服务契约（`IDownloadService`、`IDatabaseService` 等），支持依赖注入和单元测试
- **原子写入**：所有配置文件操作使用原子写入策略，防止写入中断导致数据损坏
- **Windows 原生**：深度利用 Windows 平台特性（`msvcrt` 键盘检测、`cls` 清屏、`APPDATA` 配置路径）

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │ 交互式菜单│  │ CLI 处理器│  │    Headless（无头模式）    │   │
│  │ MainMenu │  │CLIHandler│  │  脚本自动化 / 定时任务     │   │
│  └────┬─────┘  └────┬─────┘  └────────────┬─────────────┘   │
│       │              │                       │              │
├───────┼──────────────┼───────────────────────┼──────────────┤
│       ▼              ▼                       ▼              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  服务层（Services）                    │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │   │
│  │  │DownloadSvc  │ │ DatabaseSvc  │ │ TimestampSvc │  │   │
│  │  │ 下载执行    │ │ SQLite 操作  │ │ 时间戳管理    │  │   │
│  │  └─────────────┘ └──────────────┘ └──────────────┘  │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │   │
│  │  │ CookieSvc   │ │  ProxySvc    │ │  RemedySvc   │  │   │
│  │  │ 多账号管理  │ │ 代理连通性   │ │ 补救下载      │  │   │
│  │  └─────────────┘ └──────────────┘ └──────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│       │              │                       │              │
├───────┼──────────────┼───────────────────────┼──────────────┤
│       ▼              ▼                       ▼              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               基础设施层（Infrastructure）             │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐│   │
│  │  │Container │ │ TMDConfig│ │ UIHelper  │ │Validators││   │
│  │  │ DI 容器   │ │ 配置管理  │ │ UI 工具   │ │ 输入验证 ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘│   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │   │
│  │  │InputParser│ │LogParser │ │  Parsers / Formatters │  │   │
│  │  │ 智能输入  │ │ 日志解析  │ │  解析器 / 格式化工具   │  │   │
│  │  └──────────┘ └──────────┘ └──────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                             │                              │
├─────────────────────────────┼──────────────────────────────┤
│                             ▼                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    外部依赖                            │   │
│  │     tmd.exe (TMD)    │   foo.db (SQLite)            │   │
│  │     下载引擎          │   下载记录数据库              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户输入 → InputParser 解析 → CLIHandler/Menu 路由
    → DownloadService 构建参数 → subprocess 调用 tmd.exe
    → LogParser 解析输出 → DownloadResult 返回结果
    → UI 展示 / CLI 输出
```

### 关键模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| **入口** | `__main__.py` | 程序入口，初始化日志、容器、服务注册 |
| **容器** | `container.py` | 单例 DI 容器，支持实例注册与工厂延迟初始化 |
| **配置** | `config/config.py` | YAML 配置加载/保存，原子写入，字段校验 |
| **类型** | `tmd_types.py` | Protocol 接口定义 + 数据类（OperationResult, DownloadResult 等） |
| **异常** | `exceptions.py` | 统一异常层次结构（TMDError → ConfigError, DownloadError ...） |
| **CLI** | `cli/cli_handler.py` | argparse 参数解析，维护/时间戳/Profile/恢复等子命令 |
| **菜单** | `menus/*.py` | 交互式 TUI 菜单系统（MainMenu → ConfigMenu, AdvancedMenu ...） |
| **下载服务** | `services/download_service.py` | 封装 tmd.exe 子进程调用，代理环境变量，输出解析 |
| **数据库服务** | `services/database_service.py` | SQLite WAL 模式连接管理，用户/列表/时间戳 CRUD |
| **Cookie 服务** | `services/cookie_service.py` | 备用账号 YAML 管理，启用/禁用切换 |
| **代理服务** | `services/proxy_service.py` | Socket 级代理连通性检测，带 TTL 缓存 |
| **时间戳服务** | `services/timestamp_service.py` | 增量下载时间戳设置，用户/列表实体自动创建 |
| **补救服务** | `services/remedy_service.py` | 绕过 TMD 直接下载失败媒体的补救机制 |
| **UI 辅助** | `ui/ui_helper.py` | 屏幕控制、安全输入、倒计时延迟、headless 适配 |
| **输入解析** | `parsers/input_parser.py` | 智能 URL/用户名/列表ID 识别，批量输入去重 |
| **日期解析** | `parsers/date_parser.py` | 相对时间（7d/2w/1m）、绝对日期、关键字解析 |

---

## 功能特性

| 特性 | 说明 |
|------|------|
| **快捷输入** | 智能识别 URL、用户名、列表 ID，自动路由到对应下载模式 |
| **高级选项** | 精确控制、批量下载、文件导入、组合任务、时间戳管理 |
| **恢复下载** | 续传未完成任务，支持智能循环（停滞检测）和补救下载 |
| **快速下载** | 顺序下载所有配置的固定列表，自动防风控间隔 |
| **配置向导** | 交互式配置 TMD 核心参数、代理、Cookie、固定列表 |
| **时间戳管理** | 设置/重置同步时间戳，支持增量下载，自动创建用户/列表实体 |
| **Profile 下载** | 仅下载用户资料（头像、横幅、简介），不下载推文媒体 |
| **无头模式** | 适合脚本自动化，无交互提示，危险操作自动拒绝 |
| **双轨风控** | 成功/失败不同延迟策略，有效降低触发 Twitter 风控的风险 |
| **多账号管理** | 支持备用 Cookie 账号切换与整体禁用/启用 |
| **补救下载** | 绕过 TMD 核心，直接从 errors.json 下载失败媒体文件 |
| **原子配置** | 所有配置文件写入使用临时文件+rename 策略，防止数据损坏 |
| **协议接口** | 基于 Protocol 的服务抽象层，便于单元测试和扩展 |

---

## 环境依赖

### 系统要求

| 要求 | 说明 |
|------|------|
| **操作系统** | Windows 10/11（专用，使用 `msvcrt`、`cls`、`APPDATA` 等 Windows 特性） |
| **Python** | 3.8 及以上版本（3.8 ~ 3.12 经测试） |
| **前置条件** | 需要已安装 TMD (Twitter Media Downloader) 可执行文件 (`tmd.exe`) |

### Python 依赖

```bash
pip install pyyaml>=6.0
```

> **唯一运行时依赖**: PyYAML 用于配置文件的读写。其余全部使用 Python 标准库。

### 开发依赖（可选）

```bash
pip install black isort flake8 mypy pre-commit pytest
```

---

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/tmd-project/tmd-controller.git
cd tmd-controller

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install pyyaml>=6.0

# 运行
python -m tmdc
```

### 开发环境安装

```bash
# 安装开发依赖（含代码质量工具和测试框架）
pip install -e ".[dev]"

# 或手动安装各工具
pip install black>=23.3.0 isort>=5.12.0 flake8>=6.0.0 mypy>=1.3.0 pre-commit>=3.3.0 pytest>=7.0.0

# 安装 pre-commit 钩子（提交前自动检查代码质量）
pre-commit install
```

### 使用预编译版本

如果提供了 `tmdc.exe`（通过 PyInstaller 打包），可直接运行，无需安装 Python 环境：

```bash
tmdc.exe
tmdc.exe --version
tmdc.exe -u elonmusk -H
```

---

## 快速开始

### 基本用法

```bash
# 启动交互式菜单（默认）
python -m tmdc

# 显示版本
python -m tmdc --version
python -m tmdc -v

# 显示配置状态
python -m tmdc --status
python -m tmdc -s

# 调试模式（详细日志）
python -m tmdc --debug
python -m tmdc -d
```

> **推荐**: 使用 `python -m tmdc` 方式运行，直接运行 `python tmdc/__main__.py` 也可以工作，但模块方式更稳定且能正确处理包路径。

### 首次使用流程

```
1. 运行 python -m tmdc 启动程序
2. 选择 [C] 配置向导 进入配置菜单
3. 选择 [1] TMD核心配置:
     - 设置 root_path（下载根目录）
   - 输入 auth_token 和 ct0（从浏览器获取）
   - 设置 max_download_routine（0=自动）
4. （可选）选择 [3] 代理管理 配置代理服务器
5. 返回主菜单，选择 [1] 快捷输入 开始下载
```

### 获取 Cookie（必须步骤）

TMD 需要 Twitter 认证信息才能工作：

1. 打开浏览器访问 https://x.com 并登录
2. 按 `F12` 打开开发者工具
3. 切换到 **Application**（应用）标签
4. 左侧找到 **Cookies** → **https://x.com**
5. 找到以下两个值：
   - `auth_token`: 约 40 位十六进制字符串
   - `ct0`: 约 64 位以上十六进制字符串

---

## 使用方法

### 交互式菜单

```bash
python -m tmdc
```

主菜单选项：

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| **[1]** | 快捷输入 | 智能识别 URL/用户名/列表 ID 开始下载 |
| **[2]** | 高级选项 | 精确控制、批量、文件、组合、时间戳管理 |
| **[R]** | 恢复下载 | 续传未完成任务 |
| **[Q]** | 快速下载 | 顺序下载所有配置的固定列表 |
| **[C]** | 配置向导 | 配置 TMD 核心参数 |
| **[L]** | 查看日志 | 查看 TMD 运行日志（最近 50 行） |
| **[H]** | 帮助 | 查看帮助信息 |
| **[0]** | 退出 | 退出程序 |

#### 主菜单状态栏说明

启动交互式菜单后，顶部会显示实时状态栏：

```
======================================================================
        Twitter Media Downloader Controller v7.0.0
======================================================================
  可执行文件: C:\path\to\tmd.exe
  配置文件:   C:\Users\xxx\AppData\Roaming\.tmd2\conf.yaml
  状态:       [已配置] ✅
  备用账号:   [🍪 3个备用]
  固定列表:   共2个列表
  文件分批:   3行/批 [成功延迟:2-5s, 失败延迟:5-15s]
  代理设置:   127.0.0.1:7897 [🟢 开启]
```

### 快捷输入格式

| 格式 | 示例 | 说明 |
|------|------|------|
| URL | `https://x.com/elonmusk` | Twitter/X 用户主页链接 |
| URL | `https://x.com/i/lists/123456789` | 列表链接 |
| 用户名 | `@elonmusk` 或 `elonmusk` | 带 @ 或不带 @ 的用户名 |
| 列表 ID | `1234567890` | 10 位以上纯数字 |
| Name 格式 | `Elon Musk(elonmusk)` | 显示名(用户名)格式 |
| 批量输入 | `user1, user2, @user3` | 逗号或空格分隔的多个目标 |

---

### 配置向导

在主菜单选择 `[C] 配置向导` 进入配置菜单：

| 选项 | 说明 |
|------|------|
| **[1] TMD核心配置** | 设置 auth_token、ct0、下载路径、线程数 |
| **[2] 多账号管理** | 管理备用 Cookie 账号（添加/删除/启用/禁用） |
| **[3] 代理管理** | 配置代理服务器与连通性测试 |
| **[4] 固定列表管理** | 添加/删除/排序固定列表 |
| **[5] 文件下载设置** | 分批大小、双轨风控延迟 |
| **[6] 列表间间隔** | 设置 [Q] 键批量下载时的间隔（0-300 秒） |
| **[7] 迁移路径** | 修改数据库中的下载路径 |

#### Cookie 配置方式

**方式一：分别输入**
1. 配置向导 → **[1] TMD核心配置** → **[1] 修改 Cookie**
2. 分别输入 `auth_token` 和 `ct0`

**方式二：智能导入**
1. 配置向导 → **[1] TMD核心配置** → **[4] 智能导入**
2. 从浏览器开发者工具复制完整的 Cookie 字符串粘贴
3. 程序自动提取 `auth_token` 和 `ct0`

#### 代理配置

1. 选择 **[3] 代理管理**
2. 输入代理主机名（如 `127.0.0.1`）
3. 输入代理端口（如 `7890` 或 `7897`）
4. 测试代理连通性（Socket 连接检测）
5. 选择是否启用代理

#### 双轨风控延迟（防卡顿保护）

在 **[5] 文件下载设置** 中可配置：

| 设置项 | 说明 | 推荐值 |
|--------|------|--------|
| 分批大小 | 文件导入时每批处理的行数 | 3-10 |
| 成功延迟 | 批次成功后的随机延迟（秒） | 2-5 |
| 失败延迟 | 批次失败后的随机延迟（秒） | 5-15 |

> 双轨延迟机制根据上一批次的成功/失败情况选择不同的等待时间，可有效降低被 Twitter 风控限制的风险。

---

### 高级选项

在主菜单选择 `[2] 高级选项` 进入：

| 选项 | 说明 |
|------|------|
| **[1] 单个输入** | 精确控制单个用户/列表参数 |
| **[2] 批量输入** | 多用户名混合输入（单次 TMD 调用） |
| **[3] 文件导入** | 从文本文件读取任务列表（支持双轨风控延迟） |
| **[4] 关注下载** | 下载某账号的全部关注对象 |
| **[5] 组合模式** | 自定义混合任务（用户+列表+关注） |
| **[6] 禁用重试** | 单用户下载（失败不自动重试） |
| **[7] 自动关注** | 向私密账号发送关注请求 |
| **[T] 时间戳管理** | 设置/重置同步时间戳（交互式） |
| **[R] 恢复下载** | 续传未完成任务 |

#### 文件导入格式

创建文本文件（UTF-8 编码），每行一个目标：

```text
# 用户名
elonmusk
NASA

# URL 格式
https://twitter.com/elonmusk
https://x.com/NASA

# Name 格式
Elon Musk(elonmusk)

# 列表ID（以数字开头，10位以上）
1234567890
9876543210

# 注释行以 # 开头，空行忽略
```

---

### 恢复下载

当下载中断后（如 Ctrl+C 中断、网络断开），在主菜单选择 `[R] 恢复下载`：

| 选项 | 说明 |
|------|------|
| **[1] 自动恢复下载** | 循环执行恢复直到完成或检测到停滞，之后自动补救下载 |
| **[2] 恢复下载** | 单次恢复，不循环 |
| **[3] 补救下载** | 绕开 TMD，直接从 errors.json 下载失败媒体 |
| **[4] 失败任务统计** | 显示失败任务详情 |

#### 自动恢复模式的智能检测

自动恢复模式内置 **停滞检测** 机制：

1. 每轮恢复后检查待处理推文数量
2. 如果连续 N 轮（默认 3 轮）待处理数量不变，判定为"停滞"
3. 自动退出循环并执行补救下载
4. 最大轮数限制为 10 轮，防止无限循环

#### 补救下载说明

补救下载功能会：

1. 读取 `<root_path>/.data/errors.json` 中的失败任务
2. 直接使用 HTTP 请求下载媒体文件（完全绕过 TMD 核心引擎）
3. 适用于 TMD 多次恢复仍无法完成的顽固失败任务
4. 支持超时控制（30 秒）和文件大小限制（800 MB）

---

### 固定列表

#### 管理固定列表

在配置向导中选择 **[4] 固定列表管理**：

| 选项 | 说明 |
|------|------|
| **[1] 添加列表** | 添加新的固定列表（输入 10 位以上数字 ID） |
| **[2] 删除列表** | 删除已有固定列表 |
| **[3] 排序列表** | 调整列表下载顺序（上下移动） |
| **[4] 立即下载** | 选择单个列表立即下载 |

#### 批量下载固定列表

在主菜单按 **[Q]**：

- 按顺序下载所有配置的固定列表
- 支持列表间间隔设置（防止连续请求触发限流）
- 每个列表下载完成后显示进度 `(当前/总数)`
- 最终显示汇总报告（成功/失败列表及失败用户）

---

### 时间戳管理

时间戳功能用于实现 **增量下载**：只下载指定时间点之后的推文媒体，避免重复下载已有内容。

#### 设置时间戳

```bash
# 命令行方式
python -m tmdc --ts-set "user:elonmusk,7d"      # 只下载最近7天
python -m tmdc --ts-set "list:123456,2024-01-15" # 从指定日期开始
```

#### 支持的时间格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 相对天数 | `7d` | 7 天前 |
| 相对周数 | `2w` | 2 周前 |
| 相对月数 | `1m` | 1 月前（按 30 天计算） |
| 相对小时 | `3h` | 3 小时前 |
| 绝对日期 | `2024-01-15` | 指定日期（支持 `01-15` 简写，自动补全年份） |
| 日期时间 | `2024-01-15 08:30` | 指定日期和时间 |
| 关键字 | `yesterday` | 昨天此时 |
| 关键字 | `today` | 今天 00:00:00 |
| 关键字 | `now` | 当前时间 |

#### 重置时间戳

```bash
# 重置为全量下载（清除时间戳限制）
python -m tmdc --ts-reset "user:elonmusk"
python -m tmdc --ts-reset "@elonmusk"          # 简写形式
```

#### 预览模式

```bash
# 预览变更，不实际写入数据库（安全检查）
python -m tmdc --ts-set "user:elonmusk,30d" --ts-dry-run
```

#### 自动创建实体

当设置的 target 用户或列表在数据库中不存在时，会自动尝试创建对应的实体记录（需网络连接 TMD）。使用 `--ts-force` 可跳过列表操作的确认提示。

---

### Profile 下载

Profile 下载仅下载用户资料（头像、横幅、简介），**不下载**推文媒体文件。

#### 命令行方式

```bash
# 下载单个用户 Profile
python -m tmdc --profile-user elonmusk

# 下载多个用户 Profile
python -m tmdc --profile-user elonmusk --profile-user NASA

# 下载列表成员 Profile
python -m tmdc --profile-list 1234567890

# 下载多个列表成员 Profile
python -m tmdc --profile-list 111 --profile-list 222
```

---

## 命令行模式

### 基本用法

```bash
# 直接下载用户
python -m tmdc -u elonmusk

# 直接下载列表
python -m tmdc -l 1234567890

# 下载关注列表
python -m tmdc -f username

# 从文件批量导入
python -m tmdc --file users.txt

# 组合模式
python -m tmdc --combo "user1,list:123,foll:user2"

# 自动下载所有固定列表
python -m tmdc --auto-q
```

### 无头模式（Headless Mode）

无头模式适合脚本自动化和定时任务场景：

```bash
# 无头模式恢复下载（全自动循环 + 补救）
python -m tmdc -r -H

# 无头模式下载列表
python -m tmdc -l 1234567890 -H

# 无头模式组合任务
python -m tmdc --combo "user1,user2,user3" -H
```

无头模式行为：
- ✅ 无交互提示（自动跳过 pause）
- ✅ 无暂停等待（延迟变为静默 sleep）
- ⛔ 危险操作自动拒绝（explicit confirm 返回 false）
- ✅ 延迟倒计时降级为静默等待

### 恢复下载

```bash
# 交互模式：每轮结束后询问下一步
python -m tmdc -r

# 无头模式：自动持续运行直到完成（含停滞检测 + 补救下载）
python -m tmdc -r -H
```

### 显示统计

```bash
# 显示下载统计（数据库中的实体数 + 待处理失败任务数）
python -m tmdc -S
```

---

## 命令行参数详解

### 目标参数（互斥，只能选一个）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-u, --user` | string | - | 直接下载指定用户（支持 URL、@前缀、括号格式） |
| `-l, --list` | string | - | 直接下载指定列表 ID（10 位以上数字） |
| `-f, --foll` | string | - | 下载指定账号的关注列表 |
| `--file` | path | - | 从文本文件批量导入（每行一个用户名/URL，UTF-8 编码） |
| `--combo` | string | - | 组合模式（逗号分隔，格式: user1,list:123,foll:user2） |
| `--auto-q` | flag | - | 自动下载所有配置的固定列表 |
| `-r, --resume` | flag | - | 恢复未完成下载 |

### 运行模式参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-n, --no-retry` | flag | false | 禁用失败重试（单用户模式） |
| `-a, --auto-follow` | flag | false | 自动关注私密账号 |
| `-d, --dbg` | flag | false | 调试模式（详细日志输出） |
| `-H, --headless` | flag | false | 无头模式（无交互，适合脚本自动化） |
| `-c, --config` | path | - | 指定自定义配置文件路径 |

### 维护参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-S, --stats` | flag | false | 显示下载统计后退出 |
| `-v, --version` | flag | - | 显示版本号并退出 |
| `-s, --status` | flag | - | 显示配置状态 |

### 时间戳管理参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--ts-set` | string | - | 设置同步时间戳，格式: `user:username,7d` 或 `list:id,2024-01-15` |
| `--ts-reset` | string | - | 重置为初始状态（全量下载），格式: `user:username` 或 `list:id` |
| `--ts-dry-run` | flag | false | 仅预览变更，不实际写入数据库 |
| `--ts-force` | flag | false | 跳过列表操作的警告提示（脚本自动化用） |

### Profile 下载参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--profile-user` | string | - | 仅下载指定用户的 Profile（可重复使用多次） |
| `--profile-list` | string | - | 仅下载指定列表成员的 Profile（可重复使用多次） |

---

## 使用示例

### 常规下载

```bash
# 示例1：直接下载用户
python -m tmdc -u elonmusk

# 示例2：无头模式下载列表（适合脚本）
python -m tmdc -l 1234567890 -H

# 示例3：批量导入
python -m tmdc --file users.txt
```

### 高级用法

```bash
# 示例4：组合任务（用户 + 列表 + 关注）
python -m tmdc --combo "user1,list:123,foll:user2"

# 示例5：自动下载固定列表
python -m tmdc --auto-q

# 示例6：无头模式全自动恢复（推荐用于 cron/计划任务）
python -m tmdc -r -H
```

### 时间戳管理

```bash
# 示例7：增量下载（只下载最近 7 天的内容）
python -m tmdc --ts-set "user:elonmusk,7d"

# 示例8：列表从指定日期开始增量
python -m tmdc --ts-set "list:123456,2024-01-15"

# 示例9：预览变更（不写入数据库）
python -m tmdc --ts-set "user:elonmusk,30d" --ts-dry-run

# 示例10：重置为全量下载
python -m tmdc --ts-reset "user:elonmusk"
```

### Profile 下载

```bash
# 示例11：下载单个用户 Profile
python -m tmdc --profile-user elonmusk

# 示例12：批量下载多个用户 Profile
python -m tmdc --profile-user elonmusk --profile-user NASA --profile-user OpenAI

# 示例13：下载列表成员 Profile
python -m tmdc --profile-list 1234567890
```

---

## 参数兼容性速查表

| 组合 | 兼容 | 说明 |
|------|:----:|------|
| `-u` + `-H` | ✅ | 无头模式下载用户 |
| `-l` + `-H` | ✅ | 无头模式下载列表 |
| `-r` + `-H` | ✅ | 无头模式恢复下载（全自动） |
| `--combo` + `-H` | ✅ | 无头模式组合任务 |
| `--file` + `-H` | ✅ | 无头模式文件导入 |
| `--auto-q` + `-H` | ✅ | 无头模式自动列表 |
| `-u` + `-l` | ❌ | 目标参数互斥，只能选一个 |
| `--ts-set` + `--ts-reset` | ❌ | 时间戳操作互斥 |
| `--file` + `--combo` | ❌ | 目标参数互斥 |
| `-r` + `-u` | ❌ | 恢复模式不需要指定目标 |
| `--profile-user` + `--profile-list` | ✅ | 可同时使用 |
| `-S` + 其他参数 | ✅ | 统计模式可与其他参数共存 |

**符号说明**: ✅ 兼容 | ⚠️ 有条件兼容 | ❌ 不兼容

---

## 配置文件

### 配置文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 主配置 | `%APPDATA%/.tmd2/conf.yaml` | 核心配置（路径、凭证、代理、列表等） |
| 备用账号 | `%APPDATA%/.tmd2/additional_cookies.yaml` | 多账号 Cookie（可通过 `.disabled` 后缀禁用） |
| 控制器日志 | `%APPDATA%/.tmd2/tmd_controller.log` | 运行日志（RotatingFileHandler，3MB x 2） |
| TMD 数据 | `<root_path>/.data/` | TMD 核心数据目录 |
| 数据库 | `<root_path>/.data/foo.db` | 下载记录数据库（SQLite WAL 模式） |
| 失败记录 | `<root_path>/.data/errors.json` | 失败任务记录（补救下载的数据源） |

### 完整配置示例

<details>
<summary>点击查看 conf.yaml 完整配置示例</summary>

```yaml
# === TMD 核心配置 ===
root_path: ~/Downloads/twitter
max_download_routine: 0  # 0=自动(CPU核心数×10, 上限100)

# === 认证信息 ===
cookie:
  auth_token: "your_auth_token_here"   # 约40位十六进制
  ct0: "your_ct0_here"                 # 约64位以上十六进制

# === 代理配置 ===
proxy_hostname: "127.0.0.1"
proxy_tcp_port: 7897
use_proxy: true

# === 固定列表（Q键批量下载）===
quick_list_ids:
  - "1234567890"
  - "9876543210"

# === 列表间间隔（秒，范围 0-300）===
quick_list_interval: 12

# === 文件导入分批大小（范围 1-50）===
file_batch_size: 3

# === 双轨风控延迟（防卡顿保护）===
batch_delay:
  success:
    min: 2
    max: 5
  fail:
    min: 5
    max: 15
```

</details>

### 配置字段说明

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `root_path` | string | - | TMD 下载根目录（必填） |
| `max_download_routine` | int | 0 | 最大并行下载数（0=自动按 CPU×10 计算，上限 100） |
| `cookie.auth_token` | string | - | Twitter auth_token（约 40 位十六进制） |
| `cookie.ct0` | string | - | Twitter CSRF token（约 64 位以上十六进制） |
| `proxy_hostname` | string | `127.0.0.1` | 代理服务器地址 |
| `proxy_tcp_port` | int | `7897` | 代理服务器端口 |
| `use_proxy` | bool | `true` | 是否启用代理 |
| `quick_list_ids` | list | `[]` | 固定列表 ID 列表（每个元素为 10 位以上数字字符串） |
| `quick_list_interval` | int | `12` | [Q] 键批量下载时的列表间间隔（秒，0-300） |
| `file_batch_size` | int | `3` | 文件导入时每批处理的行数（1-50） |
| `batch_delay.success.min/max` | int | `0/0` | 批次成功后的随机延迟范围（秒） |
| `batch_delay.fail.min/max` | int | `0/0` | 批次失败后的随机延迟范围（秒） |

---

## 项目结构

```
tmd 新重构/
├── tmdc/                          # 主包
│   ├── __main__.py                # 程序入口（日志初始化、容器启动、服务注册）
│   ├── __init__.py                # 包初始化
│   ├── constants.py               # 常量定义（VERSION、验证阈值、超时、Twitter 保留路径）
│   ├── container.py               # 依赖注入容器（单例模式，支持工厂延迟初始化）
│   ├── exceptions.py              # 异常类层次（TMDError → ConfigError/DownloadError/...）
│   ├── tmd_types.py               # Protocol 接口 + 数据类（核心类型定义层）
│   │
│   ├── cli/                       # 命令行处理层
│   │   └── cli_handler.py         # argparse 定义 + 子命令分发（维护/时间戳/Profile/恢复）
│   │
│   ├── config/                    # 配置管理层
│   │   └── config.py              # TMDConfig 数据类（YAML 读写、原子写入、字段校验）
│   │
│   ├── menus/                     # 交互式菜单层（TUI）
│   │   ├── base_menu.py           # 抽象基类（配置检查、show 接口）
│   │   ├── main_menu.py           # 主菜单（快捷输入、Q键下载、状态栏）
│   │   ├── config_menu.py         # 配置向导菜单（7 个子选项路由）
│   │   ├── advanced_menu.py       # 高级选项菜单（批量/文件/组合/关注/时间戳）
│   │   ├── resume_menu.py         # 恢复下载菜单（自动/单次/补救/统计）
│   │   ├── timestamp_menu.py      # 时间戳管理菜单（交互式设置/重置）
│   │   ├── cookie_menu.py         # Cookie 管理菜单（增删/导入/切换）
│   │   ├── proxy_menu.py          # 代理管理菜单（配置/测试）
│   │   ├── quick_list_menu.py     # 固定列表管理（增删/排序/下载）
│   │   └── path_menu.py           # 路径迁移菜单
│   │
│   ├── parsers/                   # 解析器层
│   │   ├── input_parser.py        # 智能输入识别（URL/用户名/列表ID/批量）
│   │   ├── date_parser.py         # 日期解析（相对时间/绝对日期/关键字）
│   │   ├── delay_parser.py        # 延迟解析
│   │   └── log_parser.py          # TMD 日志解析（增量解析 DownloadResult）
│   │
│   ├── services/                  # 业务服务层（纯逻辑，无 UI 依赖）
│   │   ├── download_service.py    # 下载服务（subprocess 调用 tmd.exe）
│   │   ├── database_service.py    # 数据库服务（SQLite WAL 模式 CRUD）
│   │   ├── cookie_service.py      # Cookie 服务（备用账号 YAML 管理）
│   │   ├── proxy_service.py       # 代理服务（Socket 连通性检测 + 缓存）
│   │   ├── timestamp_service.py   # 时间戳服务（增量同步、实体自动创建）
│   │   └── remedy_service.py      # 补救下载服务（绕过 TMD 直接下载）
│   │
│   ├── ui/                        # UI 辅助层
│   │   ├── ui_helper.py           # UI 工具类（屏幕控制、输入、延迟、headless）
│   │   ├── config_checker.py      # 配置完整性检查器
│   │   └── remedy_progress.py     # 补救下载进度回调（含 SilentProgressCallback）
│   │
│   └── utils/                     # 工具函数层
│       ├── __init__.py            # 统一导出
│       ├── file_io.py             # 文件 I/O（atomic_write_yaml、backup_foo_db）
│       ├── formatters.py          # 格式化工具（时间戳、Token 脱敏、文件大小）
│       ├── path_utils.py          # 路径处理（Windows 文件名合法化、唯一路径）
│       ├── patterns.py            # 正则表达式集中定义（URL/Cookie/日志/用户名）
│       ├── text_utils.py          # 文本处理（LIKE 转义、安全拼接）
│       └── validators/            # 验证器模块
│           ├── auth.py            # auth_token / ct0 格式验证
│           ├── cookie.py          # Cookie 字符串解析
│           ├── list_id.py         # 列表 ID 合法性验证
│           ├── path.py            # 路径合法性验证
│           ├── proxy.py           # 代理参数校验
│           ├── timestamp.py       # 时间戳目标解析、数字 ID 歧义处理
│           └── username.py        # 用户名清洗与验证
│
├── tests/                         # 测试套件
│   ├── test_config.py             # 配置模块测试
│   ├── test_cli_handler_timestamp.py # CLI 时间戳处理测试
│   ├── test_container.py          # DI 容器测试
│   ├── test_constants.py          # 常量测试
│   ├── test_cookie_service.py     # Cookie 服务测试
│   ├── test_date_parser.py        # 日期解析器测试
│   ├── test_exceptions.py         # 异常类测试
│   ├── test_file_io.py            # 文件 I/O 测试
│   ├── test_formatters.py         # 格式化工具测试
│   ├── test_input_parser.py       # 输入解析器测试
│   ├── test_integration.py        # 集成测试
│   ├── test_log_parser.py         # 日志解析器测试
│   ├── test_path_utils.py         # 路径工具测试
│   ├── test_text_utils.py         # 文本工具测试
│   ├── test_timestamp_service.py  # 时间戳服务测试
│   ├── test_tmd_types.py          # 类型定义测试
│   ├── test_ui_helper.py          # UI 辅助测试
│   └── test_validators.py         # 验证器测试
│
├── build_exe.py                   # PyInstaller 打包脚本
├── tmdc.spec                      # PyInstaller 打包配置
├── pyproject.toml                  # 项目元数据与工具配置
├── requirements.txt               # Python 依赖声明
├── .pre-commit-config.yaml        # pre-commit 钩子配置
├── .flake8                        # flake8 忽略规则
├── .editorconfig                  # 编辑器统一配置
├── README.md                       # 本文档
└── .devcontainer/                 # Dev Container 配置（远程开发）
    ├── devcontainer.json
    ├── scripts/post-start.sh
    └── README.md
```

---

## 架构设计细节

### 依赖注入（DI Container）

项目使用自定义的单例 [`Container`](tmdc/container.py) 实现依赖注入：

```python
# 注册服务
container = Container.get_instance()
container.register("config", config)
container.register_factory("download_service", lambda: DownloadService(...))

# 解析服务（支持工厂延迟初始化）
ds = container.resolve("download_service")
```

关键特性：
- **单例模式**: 全局唯一的容器实例（`__new__` 控制）
- **工厂延迟初始化**: `register_factory` 支持惰性创建，首次 `resolve` 时才实例化
- **循环依赖检测**: `_resolving` 集合防止无限递归
- **便捷属性**: `container.config`、`container.logger`、`container.database_service` 等快捷属性

### 协议接口（Protocol-based Design）

[tmd_types.py](tmdc/tmd_types.py) 定义了一组 `@runtime_checkable` Protocol 接口：

| 接口 | 实现类 | 用途 |
|------|--------|------|
| `IConfig` | `TMDConfig` | 配置管理契约 |
| `IUIHelper` | `UIHelper` | UI 交互契约 |
| `IDownloadService` | `DownloadService` | 下载操作契约 |
| `IDatabaseService` | `DatabaseService` | 数据库操作契约 |
| `ICookieService` | `CookieService` | Cookie 管理契约 |
| `IProxyService` | `ProxyService` | 代理操作契约 |
| `ITimestampService` | `TimestampService` | 时间戳操作契约 |
| `IRemedyService` | `RemedyService` | 补救下载契约 |
| `IInputParser` | `InputParser` | 输入解析契约 |
| `ILogger` | `logging.Logger` | 日志记录契约 |
| `IProgressCallback` | `RemedyProgressCallback` | 进度回调契约 |

### 原子写入策略

所有配置文件写入均通过 [`atomic_write_yaml()`](tmdc/utils/file_io.py) 实现：

1. 写入临时文件（同目录 `.tmp` 后缀）
2. `os.replace()` 原子替换目标文件
3. 写入失败时原始文件不受影响
4. 异常发生时自动回滚内存中的配置对象

### 数据库设计

使用 TMD 自带的 SQLite 数据库（`foo.db`），采用 **WAL（Write-Ahead Logging）** 模式：

- `PRAGMA journal_mode=WAL` — 并发读写支持
- `PRAGMA busy_timeout=60000` — 60 秒锁等待
- `isolation_level=IMMEDIATE` — 即刻获取排他锁

主要数据表：

| 表名 | 用途 |
|------|------|
| `users` | 用户基本信息（screen_name, name, protected...） |
| `user_entities` | 用户下载实体（关联 users，含 latest_release_time 时间戳） |
| `user_links` | 用户-列表关联关系 |
| `lsts` | 列表元数据 |
| `lst_entities` | 列表下载实体（含 latest_release_time 时间戳） |

### 日志系统

双层日志架构：

| 层级 | 目的 | 配置 |
|------|------|------|
| 控制台 Handler | 实时反馈 | 级别受 `-d/--debug` 控制 |
| 文件 Handler | 持久化记录 | RotatingFileHandler（3MB × 2 个备份） |

日志位置: `%APPDATA%/.tmd2/tmd_controller.log`

---

## 开发指南

### 代码风格规范

项目强制执行以下代码质量标准：

| 工具 | 用途 | 版本要求 |
|------|------|----------|
| **black** | 代码格式化（双引号、100 字符行宽） | >= 23.3.0 |
| **isort** | 导入排序（black profile 兼容） | >= 5.12.0 |
| **flake8** | 静态代码分析（忽略 E203/W503/E501） | >= 6.0.0 |
| **mypy** | 静态类型检查（Python 3.9 基线） | >= 1.3.0 |
| **pre-commit** | Git 提交前自动执行上述检查 | >= 3.3.0 |

### 命名约定

| 元素 | 规范 | 示例 |
|------|------|------|
| 变量/函数 | `snake_case` | `download_user`, `file_batch_size` |
| 类 | `PascalCase` | `DownloadService`, `TMDConfig` |
| 常量 | `UPPER_SNAKE_CASE` | `VERSION`, `PROXY_TIMEOUT` |
| 私有成员 | `_leading_underscore` | `_db_session`, `_proxy_cache` |
| Protocol 接口 | `I` 前缀 | `IConfig`, `IDownloadService` |
| 文件名 | `snake_case` | `download_service.py` |

### 类型注解规范

- 使用 `Optional[T]` 而非 `T \| None`（兼容 Python 3.8-3.9）
- 函数签名完整注解参数和返回值
- 使用 `TYPE_CHECKING` 块避免运行时导入开销
- 数据类使用 `@dataclass` + 字段类型注解

### 文档字符串

采用 Google 风格 docstring：

```python
def download_user(self, username: str, *, timestamp: Optional[str] = None) -> DownloadResult:
    """下载用户媒体（纯业务逻辑，无输出）

    Args:
        username: Twitter 用户名
        timestamp: 时间戳过滤（可选）

    Returns:
        DownloadResult: 下载结果，包含所有信息

    Example:
        >>> result = service.download_user("elonmusk")
        >>> print(f"成功: {result.success}")
    """
```

### 运行开发工具

```bash
# 格式化所有代码
black tmdc/
isort tmdc/

# 代码检查
flake8 tmdc/

# 类型检查
mypy tmdc/

# 一次性执行所有检查（pre-commit run --all-files）
pre-commit run --all-files
```

### 添加新功能的典型流程

1. **定义类型** — 在 `tmd_types.py` 添加数据类或 Protocol 方法
2. **实现服务** — 在 `services/` 下创建或扩展服务类（纯逻辑，无 UI）
3. **注册服务** — 在 `__main__.py` 的 `_register_services()` 中注册
4. **添加菜单** — 在 `menus/` 下创建菜单类（继承 `BaseMenu`）
5. **添加 CLI** — 如需命令行支持，在 `cli_handler.py` 添加参数和处理方法
6. **编写测试** — 在 `tests/` 下添加对应测试文件
7. **运行检查** — `pre-commit run --all-files` 确保代码质量

---

## 打包发布

### 使用 PyInstaller 打包

项目提供 [`build_exe.py`](build_exe.py) 打包脚本：

```bash
# 正常打包
python build_exe.py

# 清理构建目录后重新打包
python build_exe.py --clean
```

打包产物位于 `dist/exe/tmdc.exe`。

### 打包配置 ([tmdc.spec](tmdc.spec))

PyInstaller spec 文件定义了：
- 单文件 exe 输出模式
- 隐藏的控制台窗口（`-w`）
- 收录的数据文件和资源
- UPX 压缩（可选）

---

## 测试

### 运行测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_config.py -v
pytest tests/test_input_parser.py -v

# 运行覆盖率报告
pytest tests/ --cov=tmdc --cov-report=term-missing

# 只运行失败的上次测试
pytest tests/ --lf
```

### 测试覆盖范围

| 模块 | 测试文件 | 覆盖内容 |
|------|----------|----------|
| 配置 | `test_config.py` | 加载/保存/字段校验/原子写入 |
| 容器 | `test_container.py` | 单例/注册/解析/工厂/循环检测 |
| 常量 | `test_constants.py` | 常量值/别名 |
| 类型 | `test_tmd_types.py` | 数据类构造/属性/合并 |
| 异常 | `test_exceptions.py` | 异常层次/消息格式 |
| 输入解析 | `test_input_parser.py` | URL/用户名/列表/批量/括号格式 |
| 日期解析 | `test_date_parser.py` | 相对时间/绝对日期/关键字 |
| Cookie 服务 | `test_cookie_service.py` | 加载/保存/增删/禁用切换 |
| 时间戳服务 | `test_timestamp_service.py` | 设置/重置/批量/自动创建 |
| UI 辅助 | `test_ui_helper.py` | 延迟/输入/确认/headless |
| 文件 I/O | `test_file_io.py` | 原子写入/备份/路径工具 |
| 格式化 | `test_formatters.py` | 时间戳/脱敏/文件大小 |
| 路径工具 | `test_path_utils.py` | 文件名合法化/唯一路径 |
| 文本工具 | `test_text_utils.py` | LIKE 转义/拼接 |
| 验证器 | `test_validators.py` | 全部验证函数 |
| 日志解析 | `test_log_parser.py` | 增量解析/错误提取 |
| CLI 时间戳 | `test_cli_handler_timestamp.py` | CLI 参数解析/执行流程 |
| 配置检查 | `test_config_checker.py` | 完整性校验逻辑 |
| 集成测试 | `test_integration.py` | 端到端流程验证 |

---

## 常见问题

### Q: 找不到 TMD 可执行文件？

**症状**: 启动时显示 `⚠️ 未找到 TMD 可执行文件`

**解决**: 确保 `tmd.exe` 位于以下位置之一：
- 系统 `PATH` 环境变量中的任意目录
- 与 `tmdc/` 包同级目录
- `tmd/` 子目录中

程序查找顺序：`where 命令` → 同级目录 → `tmd/` 子目录

### Q: Cookie 失效怎么办？

**症状**: 下载失败，提示认证错误或 403

**解决**:
1. 重新登录 https://x.com 并获取新的 `auth_token` 和 `ct0`
2. 配置向导 → **[1] TMD核心配置** → 更新 Cookie
3. 或使用 **[2] 多账号管理** 切换到其他可用账号

### Q: 代理连接失败？

**症状**: 无法连接到 Twitter，超时错误

**排查步骤**:
1. 确认代理软件（Clash/V2Ray 等）正在运行
2. 检查代理端口是否正确（默认 7897）
3. 在配置向导 **[3] 代理管理** 中测试连通性
4. 如果使用 HTTP 代理而非 SOCKS5，确保协议匹配

### Q: 下载中断如何恢复？

**症状**: 下载过程中断（Ctrl+C、网络中断等）

**解决**:
1. 重新启动程序
2. 选择 **[R] 恢复下载** → **[1] 自动恢复下载**
3. 程序会自动循环恢复直到完成或检测到停滞
4. 停滞后自动执行补救下载处理顽固失败

> 已下载的文件是安全的，不会重复下载

### Q: Windows 路径过长怎么办？

**症状**: `FileNotFoundError` 或路径超过 260 字符的错误

**解决**:
1. 缩短 `root_path`（下载根目录），尽量靠近磁盘根目录
2. 使用配置向导 **[7] 迁移路径** 功能修改数据库中的路径
3. 或在 Windows 中启用长路径支持（组策略）

### Q: 什么是无头模式？何时使用？

无头模式（`-H` / `--headless`）专为 **脚本自动化** 场景设计：

| 特性 | 交互模式 | 无头模式 |
|------|----------|----------|
| 交互提示 | ✅ 正常显示 | ❌ 自动跳过 |
| 暂停等待 | ✅ 正常暂停 | ❌ 自动跳过 |
| 危险操作 | 需要确认 | 自动拒绝 |
| 延迟显示 | 倒计时 + 可跳过 | 静默 sleep |
| 适用场景 | 手动操作 | cron/计划任务/CI |

**典型用法**: `python -m tmdc -r -H` 放入 Windows 计划任务定时执行

### Q: 如何规避 Twitter 风控限制？

**症状**: 频繁下载后出现速率限制或临时封禁

**建议**:
1. 启用双轨风控延迟（配置向导 **[5]**）：成功 2-5s / 失败 5-15s
2. 降低文件分批大小（如从 5 降到 3）
3. 使用多账号轮询（配置向导 **[2]** 添加备用账号）
4. 合理设置列表间间隔（建议 12-30 秒）

### Q: 列表下载不完整？

**症状**: 列表成员下载部分成功、部分失败

**可能原因与解决**:
1. **私密列表** — 确认你的账号可以访问该列表
2. **Cookie 过期** — 更新认证信息
3. **网络不稳定** — 使用恢复下载重试
4. **账号权限不足** — 列表所有者可能限制了访问

### Q: 数据库被锁定？

**症状**: `database is locked` 错误

**原因**: 另一个 tmdc 或 tmd 进程正在使用数据库

**解决**:
1. 确保没有其他 tmdc 实例在运行
2. 确保没有残留的 tmd.exe 进程（任务管理器结束）
3. 如果问题持续，重启后 `foo.db` 会自动备份

### Q: 如何查看详细调试信息？

```bash
# 启用调试模式（控制台和文件都输出 DEBUG 级别日志）
python -m tmdc --debug

# 查看日志文件
type "%APPDATA%\.tmd2\tmd_controller.log"
```

---

## 更新日志

### v7.0.0（当前版本）

**重大重构版本**：

- 🏗️ **架构重构**: 完全模块化架构（services/menus/parsers/ui/utils 分层）
- 🔬 **依赖注入**: 新增 `Container` 单例 DI 容器，支持工厂延迟初始化
- 📐 **协议接口**: 基于 `Protocol` 的服务抽象层，支持类型检查和 Mock 测试
- 🛡️ **双轨风控**: 成功/失败不同延迟策略，有效降低风控风险
- 👤 **Profile 下载**: 新增 `--profile-user` / `--profile-list` 参数
- ⏰ **时间戳 CLI**: 新增 `--ts-set` / `--ts-reset` 命令行时间戳管理
- 🤖 **无头模式**: 新增 `-H/--headless` 参数，支持脚本自动化
- 💾 **原子写入**: 所有配置文件操作使用原子写入策略
- 🔄 **智能恢复**: 恢复下载新增停滞检测 + 自动补救下载
- 🍪 **多账号管理**: 新增备用 Cookie 账号的完整生命周期管理
- 📁 **路径迁移**: 新增数据库路径批量迁移功能
- 📊 **状态栏增强**: 主菜单实时显示配置/代理/账号/列表状态
- 🧹 **异常体系**: 统一的异常类层次结构（TMDError 及其子类）
- 📝 **类型系统**: 完整的数据类体系（DownloadResult, OperationResult, ProxyStatus ...）

---

## 注意事项

1. ⚠️ 本程序为 **Windows 专用版**，使用了 `msvcrt`、`os.system("cls")`、`%APPDATA%` 等 Windows 特性
2. 🔑 使用前必须配置 `auth_token` 和 `ct0`（通过配置向导或编辑 conf.yaml）
3. ⏱️ 大型列表（数千成员）下载可能需要很长时间，可随时按 `Ctrl+C` 安全暂停
4. ⏰ 时间戳设置后立即生效，下次下载将只获取该时间点之后的推文媒体
5. 📄 Profile 下载仅获取用户资料（头像/横幅/简介），**不会**下载推文媒体
6. 🛡️ 使用 `--ts-dry-run` 可预览时间戳变更，避免误操作数据库
7. 📦 打包后的 `tmdc.exe` 可独立运行，无需安装 Python 环境

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 贡献流程

1. **Fork** 本仓库
2. **创建特性分支**: `git checkout -b feature/amazing-feature`
3. **遵循代码规范**: 确保代码通过 `pre-commit run --all-files`
4. **编写测试**: 为新功能添加对应的测试用例
5. **提交更改**: `git commit -m 'Add some amazing feature'`
6. **推送到分支**: `git push origin feature/amazing-feature`
7. **创建 Pull Request**

### 代码提交规范

- 提交信息使用英文，清晰描述变更内容
- 每个 commit 保持原子性（单一功能点）
- 在 PR 描述中说明变更的原因和影响范围

### Bug 反馈

请使用 GitHub Issues 提交 bug，包含以下信息：
- tmdc 版本号（`python -m tmdc --version`）
- Python 版本
- Windows 版本
- 复现步骤
- 期望行为 vs 实际行为
- 相关日志（`--debug` 模式下的输出）

---

*最后更新: 2026-04-04 | 版本: v7.0.0*

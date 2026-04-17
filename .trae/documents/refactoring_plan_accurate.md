# TMDC 代码重构准确计划

## 重要发现：原计划中的许多"死代码"实际上并非死代码！

经过详细分析，原计划中标记为"死代码"的很多项目实际上**仍在被使用**。以下是准确的分析结果：

***

## 一、真正可以安全删除的代码 ✅

### 1.1 已不存在的代码（可能之前已删除）

| 项目                            | 原计划位置                         | 实际情况                                      |
| ----------------------------- | ----------------------------- | ----------------------------------------- |
| `ProxyService.save_config()`  | `services/proxy_service.py`   | **已不存在**。当前代码中只有 `save_proxy_config()` 方法 |
| `utils/validators/path.py`    | `utils/validators/path.py`    | **文件已不存在**                                |
| `utils/validators/list_id.py` | `utils/validators/list_id.py` | **文件已不存在**                                |

### 1.2 确认无用的代码

| 项目                   | 位置                | 验证结果          | 操作    |
| -------------------- | ----------------- | ------------- | ----- |
| `_check_protocol` 函数 | `ui/ui_helper.py` | 无任何调用，仅用于类型检查 | ✅ 可删除 |

***

## 二、已完成的删除操作 ✅

### 2.1 删除的测试文件

以下测试文件仅测试已删除的代码，已被删除：

| 文件                         | 说明                   |
| -------------------------- | -------------------- |
| `tests/test_exceptions.py` | 测试已删除的 exceptions 模块 |
| `tests/test_file_io.py`    | 测试已删除的 file\_io 函数   |
| `tests/test_formatters.py` | 测试已删除的 formatters 函数 |
| `tests/test_text_utils.py` | 测试已删除的 safe\_join 函数 |

### 2.2 精确修改的测试文件

使用 SearchReplace 精确删除与已删除代码相关的测试方法：

| 文件                                    | 删除内容                                                                                                       |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `tests/test_timestamp_service.py`     | `TestFormatTimestampDisplay` 类（3个测试方法）、`TestFormatDuration` 类（1个测试方法）                                      |
| `tests/test_validators.py`            | `TestValidatePath` 类、`TestValidateListId` 类、`TestValidateUsername` 类                                       |
| `tests/test_container.py`             | `test_get_service_singleton`、`test_get_service_creates_instance`、`test_get_service_returns_existing` 等测试方法 |
| `tests/test_ui_helper.py`             | `TestShowBatchSummary` 类（4个测试方法）、`TestCheckProtocol` 类（3个测试方法）                                             |
| `tests/test_cli_handler_timestamp.py` | 更新 mock 配置：`find_users_for_reset` → `find_users`                                                           |

***

## 三、不能删除的代码 ❌

### 3.1 业务代码正在使用

| 项目                   | 位置                     | 使用位置                              | 说明                 |
| -------------------- | ---------------------- | --------------------------------- | ------------------ |
| `USERNAME_MAX_LEN`   | `utils/patterns.py`    | `parsers/input_parser.py:133,145` | 用于验证用户名长度          |
| `C.USERNAME_MAX_LEN` | `constants.py`         | `utils/patterns.py:27`            | 被 patterns.py 导入使用 |
| `check_reachable`    | `proxy_service.py:144` | 自身内部调用                            | 方法内部调用，不能删除        |

***

## 四、修正后的重构建议

### 阶段 1：安全删除（确认无用）

1. ✅ 删除 `ui/ui_helper.py` 中的 `_check_protocol` 函数

### 阶段 2：已完成的测试清理

✅ **已完成**：删除了仅测试已删除代码的测试文件和方法

### 阶段 3：原计划中的其他修改（仍需执行）

以下原计划中的修改仍然有效：

1. **合并** **`DatabaseService.find_users()`** **和** **`find_users_for_reset()`** - 需要更新
2. **合并** **`DatabaseService._db_session()`** **和** **`db_session()`** - 需要更新
3. **删除** **`DatabaseService._escape_like_pattern()`** - 需要更新
4. **删除** **`DatabaseService.check_list_exists()`** **别名** - 需要更新调用方
5. **合并** **`DownloadService.check_list_exists()`** **和** **`_check_list_exists()`** - 需要更新
6. **删除** **`CookieService.load_cookies()`** **/** **`save_cookies()`** **别名** - 需要更新调用方
7. **合并** **`ProxyService.check_reachable()`** **和** **`check_proxy_reachable()`** - 需要更新
8. **删除** **`TimestampService`** **的委托方法** - 需要更新调用方
9. **删除** **`CLIHandler`** **的委托方法** - 需要更新
10. **提取公共的** **`_get_requests()`** **函数** - 需要更新
11. **提取时区剥离共享逻辑** - 可以执行
12. **修复** **`escape_like_pattern`** **参数** - 可以执行
13. **删除过时注释** - 可以执行

***

## 五、执行建议

### 执行顺序

1. **先执行阶段 1**（安全删除）
2. **运行测试** 确保无回归
3. **执行阶段 3**（原计划中的有效修改）
4. **每批修改后运行测试**

### 测试命令

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_timestamp_service.py -v
python -m pytest tests/test_validators.py -v
python -m pytest tests/test_container.py -v
```

***

## 六、总结

| 类别          | 数量 | 说明                                                                                  |
| ----------- | -- | ----------------------------------------------------------------------------------- |
| ✅ 可安全删除     | 1项 | 确认无任何使用                                                                             |
| ✅ 已删除测试文件   | 4个 | `test_exceptions.py`, `test_file_io.py`, `test_formatters.py`, `test_text_utils.py` |
| ✅ 已精确修改测试文件 | 5个 | 使用 SearchReplace 删除相关测试方法                                                           |
| ❌ 业务代码使用    | 3项 | 不能删除                                                                                |

### 关键教训

1. **原代码质量分析工具可能将"仅测试使用的代码"误判为"死代码"**。在执行删除操作前，必须手动验证代码的实际使用情况。

2. **遵循 CLAUDE.md 第3条：外科手术式修改**：

   * 只改必须改的内容

   * 用 SearchReplace 精确编辑，绝不重写整个文件

   * 不要"顺手优化"相邻代码

### 当前测试状态

* **测试总数**: 288 个

* **通过**: 288 个

* **失败**: 0 个


# TMDC 代码审查报告：冗余/死代码/不必要包装/不必要代码

## 审查范围

对 `tmdc/` 下所有 `.py` 源文件进行全面审查，识别以下问题：
1. **冗余代码** — 功能重复的实现
2. **死代码** — 未被任何地方调用的函数/方法/类/变量
3. **不必要包装函数** — 仅转发调用、无额外逻辑的中间层
4. **不必要代码** — 过度设计、无实际用途的代码

---

## 一、冗余代码（功能重复）

### 1.1 `_get_requests()` 延迟导入函数重复定义
- **文件**: `proxy_service.py:32-42` 和 `remedy_service.py:45-59`
- **问题**: 两个文件各自定义了完全相同的 `_get_requests()` 延迟导入函数和模块级 `_requests` 变量
- **建议**: 提取到 `utils/` 下的公共模块中，两处共享

### 1.2 `DatabaseService.find_users()` 与 `find_users_for_reset()` 高度重复
- **文件**: `database_service.py:134-182` 和 `database_service.py:184-225`
- **问题**: 两个方法的 SQL 查询完全相同，唯一区别是 `find_users_for_reset` 默认 limit=50 且使用参数化 LIMIT
- **调用方**: `find_users` 被 `advanced_menu.py:561` 和 `cli_handler.py:421` 调用；`find_users_for_reset` 被 `cli_handler.py:641` 调用
- **建议**: 合并为一个方法 `find_users(keyword, limit=None, default_limit=50)`

### 1.3 `DatabaseService._db_session()` 与 `db_session()` 重复
- **文件**: `database_service.py:80-106` 和 `database_service.py:107-117`
- **问题**: `db_session()` 是 `_db_session()` 的公共包装，仅 `with self._db_session() as cursor: yield cursor`
- **建议**: 将 `_db_session` 改名为 `db_session`（公共），删除包装层

### 1.4 `DatabaseService._escape_like_pattern()` 纯委托
- **文件**: `database_service.py:121-130`
- **问题**: 仅调用 `escape_like_pattern(keyword)` 并返回
- **建议**: 删除此方法，调用处直接使用 `escape_like_pattern()`

### 1.5 `DatabaseService.check_list_exists()` 是 `check_list_metadata_exists()` 的别名
- **文件**: `database_service.py:300-311`
- **问题**: `check_list_exists` 仅 `return self.check_list_metadata_exists(list_id)`，已标记为 Deprecated
- **调用方**: `advanced_menu.py:1053`, `cli_handler.py:708`, `download_service.py:355`
- **建议**: 统一使用 `check_list_metadata_exists`，删除 `check_list_exists`

### 1.6 `DownloadService.check_list_exists()` 是 `_check_list_exists()` 的无意义包装
- **文件**: `download_service.py:279-289` 和 `download_service.py:341-355`
- **问题**: 公共方法 `check_list_exists` 仅调用私有方法 `_check_list_exists`
- **建议**: 删除 `_check_list_exists`，将逻辑直接放在 `check_list_exists` 中

### 1.7 `CookieService.load_cookies()` / `save_cookies()` 是 `load_additional_cookies()` / `save_additional_cookies()` 的纯别名
- **文件**: `cookie_service.py:58-64`
- **问题**: 纯转发调用
- **调用方**: `load_cookies` 被 `main_menu.py:180` 调用
- **建议**: 保留一组命名，删除别名

### 1.8 `ProxyService.save_config()` 是 `save_proxy_config()` 的纯转发（无外部调用者）
- **文件**: `proxy_service.py:129-149`
- **问题**: 无任何外部调用者
- **建议**: 删除 `save_config` 方法

### 1.9 `ProxyService.check_reachable()` 与 `check_proxy_reachable()` 逻辑重叠
- **文件**: `proxy_service.py:75-98` 和 `proxy_service.py:100-127`
- **调用方**: `check_reachable` 被内部调用；`check_proxy_reachable` 被 `proxy_menu.py` 多处调用
- **建议**: 合并为一个方法 `check_reachable(timeout, use_cache=True)`

### 1.10 `TimestampService.format_timestamp_display()` 和 `format_duration()` 纯委托
- **文件**: `timestamp_service.py:67-92`
- **调用方**: `format_timestamp_display` 被 `timestamp_menu.py:95,126` 调用
- **建议**: 删除委托方法，调用方直接使用 `utils.formatters` 中的函数

### 1.11 `CLIHandler._parse_ts_arg()` 纯委托
- **文件**: `cli_handler.py:543-559`
- **调用方**: `cli_handler.py:508,529`（内部调用）
- **建议**: 删除此方法，调用处直接使用 `parse_timestamp_target()`

### 1.12 `CLIHandler._get_errors_path()` 纯委托
- **文件**: `cli_handler.py:381-383`
- **调用方**: `cli_handler.py:351`（内部调用）
- **建议**: 删除此方法，调用处直接使用 `get_errors_json_path()`

---

## 二、死代码（未被调用）

### 2.1 `exceptions.py` 整个模块未被使用
- **文件**: `exceptions.py`
- **问题**: 定义了 8 个异常类，但整个项目中没有任何地方 import 或 raise
- **建议**: 删除整个模块

### 2.2 `tmd_types.py` 中多个数据类/类型未被使用
- **未使用的数据类**: `UserInfo`, `ListInfo`, `CookieInfo`, `BatchConfig`, `MenuOption`
- **未使用的类型别名**: `PathLike`, `JsonValue`, `CookieDict`
- **未使用的类型变量**: `T`, `TConfig`, `TService`
- **未使用的工具函数**: `create_logger()`
- **建议**: 删除所有未使用的定义

### 2.3 `tmd_types.py` 中未使用的方法/属性
- `OperationResult.has_message` / `has_error` (L1198-1206)
- `BatchOperationResult.is_partial_success` (L1237-1239)
- `DownloadResult.merge()` (L1321-1339)
- `DownloadResult.get_start_message()` (L1309-1319)
- `ProxyStatus.error_message` / `status_text` (L1423, 1431-1437)
- **建议**: 删除

### 2.4 `utils/formatters.py` 中未使用的函数
- `format_file_size()` (L148-184)
- `format_number()` (L187-217)
- **建议**: 删除

### 2.5 `utils/file_io.py` 中未使用的函数
- `read_file_lines()` (L172-217)
- `get_file_size()` (L220-244)
- `ensure_dir()` (L151-169)
- **建议**: 删除

### 2.6 `utils/text_utils.py` 中未使用的函数
- `safe_join()` (L39-60)
- **建议**: 删除

### 2.7 `utils/validators/` 中未使用的验证器
- `path.py` - `validate_path()` 整个模块未使用
- `list_id.py` - `validate_list_id()` 整个模块未使用
- `username.py` - `validate_username()` 函数未使用（`clean_username` 和 `is_reserved_path` 有使用）
- **建议**: 删除未使用的文件和函数

### 2.8 `patterns.py` 中重复常量
- `USERNAME_MAX_LEN = 15` 与 `Constants.USERNAME_MAX_LEN` 重复
- **建议**: 删除 `patterns.py` 中的定义

### 2.9 `ui_helper.py` 中未使用的函数
- `_check_protocol()` (L523-528)
- `show_batch_summary()` (L490-519) - 无调用者，且有 f-string bug
- **建议**: 删除

### 2.10 `DownloadService` 中未使用的参数
- `download_user()` 和 `download_list()` 中的 `timestamp` 参数
- **建议**: 删除未使用的参数

### 2.11 `container.py` 中未使用的函数
- `get_service()` (L132-134)
- **建议**: 删除

### 2.12 `__main__.py` 中重复导入
- `_find_tmd_executable` 函数内部重复 `import sys`
- `_shutdown_logging` 函数内部重复 `import logging`
- **建议**: 删除函数内部的重复导入

---

## 三、不必要包装函数（仅转发调用）

| 包装函数 | 实际函数 | 位置 |
|---------|---------|------|
| `DatabaseService.db_session()` | `_db_session()` | database_service.py:107-117 |
| `DatabaseService._escape_like_pattern()` | `escape_like_pattern()` | database_service.py:121-130 |
| `DownloadService._check_list_exists()` | `check_list_exists()` | download_service.py:341-355 |
| `CookieService.load_cookies()` | `load_additional_cookies()` | cookie_service.py:58-61 |
| `CookieService.save_cookies()` | `save_additional_cookies()` | cookie_service.py:62-64 |
| `ProxyService.save_config()` | `save_proxy_config()` | proxy_service.py:129-149 |
| `TimestampService.format_timestamp_display()` | `format_timestamp()` | timestamp_service.py:67-78 |
| `TimestampService.format_duration()` | `format_duration()` | timestamp_service.py:80-92 |
| `CLIHandler._parse_ts_arg()` | `parse_timestamp_target()` | cli_handler.py:543-559 |
| `CLIHandler._get_errors_path()` | `get_errors_json_path()` | cli_handler.py:381-383 |
| `BaseMenu._check_config_or_return()` | `ConfigChecker.check_basic_config()` | base_menu.py:64-81 |

---

## 四、不必要代码（过度设计）

### 4.1 Protocol 接口过度定义
- 定义了 10 个 `@runtime_checkable` Protocol，但每个都只有一个实现类
- `runtime_checkable` 装饰器也未被利用
- **建议**: 可保留但去除 `@runtime_checkable`

### 4.2 `IRemedyService` 接口与实现不匹配
- 定义了 `ui: IUIHelper` 属性，但实现使用 `IProgressCallback`
- `execute()` 签名不匹配
- **建议**: 修正 Protocol 定义

### 4.3 `Container` 属性访问器模式
- 为多个服务写了属性，但服务总是通过 `_register_services` 注册
- fallback 逻辑从未执行
- **建议**: 删除这些属性，统一使用 `resolve()`

### 4.4 `UIHelper` 的 print 方法无差异化
- `print_success`/`print_error`/`print_warning`/`print_info` 实现完全相同
- **建议**: 添加差异化前缀或删除

---

## 五、实施优先级

### 高优先级（删除无风险）
1. 删除 `exceptions.py` 整个模块
2. 删除 `tmd_types.py` 中未使用的数据类、类型别名、类型变量、方法
3. 删除 `utils/validators/path.py` 和 `list_id.py` 整个文件
4. 删除 `utils/validators/username.py` 中的 `validate_username()`
5. 删除 `formatters.py` 中 `format_file_size()`, `format_number()`
6. 删除 `file_io.py` 中 `read_file_lines()`, `get_file_size()`, `ensure_dir()`
7. 删除 `text_utils.py` 中 `safe_join()`
8. 删除 `ui_helper.py` 中 `_check_protocol()` 和 `show_batch_summary()`
9. 删除 `container.py` 中 `get_service()`
10. 删除 `ProxyService.save_config()`
11. 删除 `patterns.py` 中重复的 `USERNAME_MAX_LEN`
12. 删除 `__main__.py` 中函数内部的重复导入
13. 同步清理所有 `__init__.py` 和 `__all__`

### 中优先级（需更新调用方）
14. 合并 `DatabaseService.find_users()` 和 `find_users_for_reset()`
15. 合并 `DatabaseService._db_session()` 和 `db_session()`
16. 删除 `DatabaseService._escape_like_pattern()`
17. 删除 `DatabaseService.check_list_exists()` 别名
18. 合并 `DownloadService.check_list_exists()` 和 `_check_list_exists()`
19. 删除 `CookieService.load_cookies()`/`save_cookies()` 别名
20. 合并 `ProxyService.check_reachable()` 和 `check_proxy_reachable()`
21. 删除 `TimestampService.format_timestamp_display()` 和 `format_duration()`
22. 删除 `CLIHandler._parse_ts_arg()` 和 `_get_errors_path()`
23. 提取公共的 `_get_requests()` 延迟导入函数

### 低优先级（架构优化）
24. 精简 `Container` 属性访问器
25. 修正 `IRemedyService` Protocol 定义
26. 统一 `UIHelper` 的 print 方法
27. 评估 Protocol 接口的必要性

---

## 六、预期收益

- **删除代码量**: 预计可删除约 500-700 行冗余/死代码
- **文件删除**: 可删除 2 个完整的验证器文件和 1 个异常模块
- **维护性提升**: 减少重复逻辑，降低修改时遗漏的风险

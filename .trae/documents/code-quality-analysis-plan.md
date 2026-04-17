# 代码质量分析计划

## 分析范围

对 `tmdc` 项目中所有 `.py` 源代码文件进行全面代码质量分析，重点识别：冗余代码、死代码、不必要的代码。

***

## 分析步骤

### 步骤 1：死代码识别与标记

通过交叉引用分析，以下函数/变量/类型仅在定义处和 `__init__.py` 导出处出现，**从未被业务代码实际调用**：

| #   | 类型   | 名称                  | 文件                             | 行号   | 风险等级 | 说明                              |
| --- | ---- | ------------------- | ------------------------------ | ---- | ---- | ------------------------------- |
| D1  | 函数   | `get_file_size`     | `utils/file_io.py`             | L220 | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D2  | 函数   | `read_file_lines`   | `utils/file_io.py`             | L172 | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D3  | 函数   | `ensure_dir`        | `utils/file_io.py`             | L151 | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D4  | 函数   | `format_file_size`  | `utils/formatters.py`          | L148 | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D5  | 函数   | `format_number`     | `utils/formatters.py`          | L187 | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D6  | 函数   | `safe_join`         | `utils/text_utils.py`          | L39  | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D7  | 函数   | `validate_path`     | `utils/validators/path.py`     | L10  | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D8  | 函数   | `validate_list_id`  | `utils/validators/list_id.py`  | L9   | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D9  | 函数   | `validate_username` | `utils/validators/username.py` | L13  | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务调用 |
| D10 | 类型别名 | `PathLike`          | `tmd_types.py`                 | L46  | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务使用 |
| D11 | 类型别名 | `JsonValue`         | `tmd_types.py`                 | L49  | 低    | 仅在定义处和 `__init__.py` 导出，无任何业务使用 |

**影响评估**：这些死代码增加了维护负担和包体积，但不影响运行时性能。建议标记为待清理。

### 步骤 2：冗余代码识别与标记

| #  | 类型   | 名称                                              | 文件                              | 行号                 | 风险等级 | 说明                                                                           |
| -- | ---- | ----------------------------------------------- | ------------------------------- | ------------------ | ---- | ---------------------------------------------------------------------------- |
| R1 | 冗余包装 | `_escape_like_pattern`                          | `services/database_service.py`  | L121-130           | 低    | 纯委托方法，仅调用 `escape_like_pattern(keyword)`，无额外逻辑，可直接使用原函数                      |
| R2 | 冗余委托 | `TimestampService.format_timestamp_display`     | `services/timestamp_service.py` | L67-81             | 低    | 纯委托方法，仅调用 `format_timestamp(timestamp, default_empty=default_empty)`，无任何额外逻辑 |
| R3 | 冗余委托 | `TimestampService.format_duration`              | `services/timestamp_service.py` | L83-92             | 低    | 纯委托方法，仅调用 `format_duration(td)`，无任何额外逻辑                                      |
| R4 | 重复逻辑 | `format_timestamp` 与 `parse_db_timestamp` 的时区处理 | `utils/formatters.py`           | L92-98 vs L248-253 | 中    | 两个函数包含完全相同的时区剥离逻辑（`+` 号和 `Z` 结尾处理），应提取为共享内部函数                                |
| R5 | 过时注释 | `parse_cookie_string 已移除` 注释                    | `tmd_types.py`                  | L949-950           | 低    | 迁移已完成，注释已无信息价值                                                               |

**影响评估**：

* R1-R3 的冗余包装增加了不必要的调用层级，影响代码可读性

* R4 的重复逻辑增加维护风险，修改一处时容易遗漏另一处

* R5 的过时注释造成困惑

### 步骤 3：不必要的代码识别与标记

| #  | 类型    | 名称                                       | 文件                    | 行号     | 风险等级 | 说明                                                                                                                                                                          |
| -- | ----- | ---------------------------------------- | --------------------- | ------ | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| U1 | 不必要导入 | `__init__.py` 中导出大量未被外部使用的函数             | `utils/__init__.py`   | L15-66 | 低    | `get_file_size`, `read_file_lines`, `ensure_dir`, `format_file_size`, `format_number`, `safe_join`, `validate_path`, `validate_list_id`, `validate_username` 等被导出但从未被外部模块使用 |
| U2 | 不必要参数 | `escape_like_pattern` 的 `escape_char` 参数 | `utils/text_utils.py` | L14    | 低    | 参数 `escape_char` 定义但从未在函数体内使用，函数内部硬编码了 `\\` 作为转义字符                                                                                                                          |

**影响评估**：

* U1 增加了模块的公共 API 表面积，使代码意图不清晰

* U2 是接口与实现不一致的隐患

> **注**：经确认，`tmd_types.py` 中的 `contextmanager`（L558 使用）、`Callable`（L1528 使用）、`Generator`（L561 使用）、`TypeVar`（L1533-1539 使用）均有实际使用，不属于未使用导入。

***

## 问题分类统计

| 类别        | 数量     | 风险等级分布        |
| --------- | ------ | ------------- |
| 死代码 (D)   | 11     | 低:11          |
| 冗余代码 (R)  | 5      | 低:4, 中:1      |
| 不必要代码 (U) | 2      | 低:2           |
| **合计**    | **18** | **低:17, 中:1** |

## 风险等级评估

* **低风险**（17项）：不影响程序功能，清理后可提升可维护性和代码整洁度

* **中风险**（1项，R4）：重复逻辑存在维护风险，修改一处时容易遗漏另一处，可能导致行为不一致

## 优化建议

1. **死代码清理**（D1-D11）：建议逐步移除未被使用的函数和类型别名，同时清理对应的 `__init__.py` 导出。如果考虑未来可能使用，可先添加 `# TODO: 待确认是否需要` 标记。

2. **冗余包装消除**（R1-R3）：

   * R1: 将 `_escape_like_pattern` 的调用处直接替换为 `escape_like_pattern`

   * R2-R3: 调用方直接使用 `format_timestamp` 和 `format_duration`，移除 `TimestampService` 中的委托方法

3. **重复逻辑提取**（R4）：将时区剥离逻辑提取为 `_strip_timezone(ts_str: str) -> str` 内部函数，供 `format_timestamp` 和 `parse_db_timestamp` 共用

4. **过时注释清理**（R5）：移除 `tmd_types.py` 中的迁移完成注释

5. **未使用参数修复**（U2）：移除 `escape_like_pattern` 的 `escape_char` 参数，或在函数体内使用该参数

6. **未使用导入清理**：`tmd_types.py` 中的 `contextmanager`、`Callable`、`Generator`、`TypeVar` 经确认均有实际使用，无需清理

7. **导出精简**（U1）：将 `utils/__init__.py` 中未被外部使用的导出移除，保持公共 API 最小化

## 执行顺序

1. 清理死代码 D1-D11 及对应导出 U1
2. 消除冗余包装 R1-R3
3. 提取共享逻辑修复 R4
4. 修复 U2 未使用参数
5. 清理 R5 过时注释
6. 运行测试验证无回归


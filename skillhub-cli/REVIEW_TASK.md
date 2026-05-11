请审查 skillhub-cli/src/skillhub/ 下的所有 Python 文件，检查并修复：
1. Python 3.10 兼容性（str | None 需要 from __future__ import annotations）
2. import toml 改为 try import tomllib (3.11+) else toml
3. 异常处理完整性
4. 语法正确性

发现问题直接修复文件，最后列出所有修改。

# ai-ticket-ai-service

这是 `ai-ticket-platform` 的独立 FastAPI AI 能力服务。它负责模型调用、结构化输出、回复草稿、受控只读 Agent、轻量 RAG 和 MCP 演示；Java 仍然是用户认证、授权、工单数据、事务和业务决策的可信边界。Python 不连接 Java MySQL，也不直接修改 `tickets`。

本仓库的定位是 AI capability service，而不是第二套业务后端：浏览器不直接访问 Python，Java 通过受控内部 HTTP 调用本服务。

## 技术栈

- Python 3.11+
- FastAPI、Uvicorn、Pydantic Settings
- OpenAI-compatible provider adapter + deterministic fake provider
- 官方 MCP Python SDK
- pytest、HTTPX TestClient

## 运行

需要 Python 3.11+：

```powershell
python -m pip install -e ".[test]"
pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

健康检查：

```text
GET http://127.0.0.1:8000/health
```

内部接口需要 `X-Internal-AI-Token`。默认值仅用于本地开发；真实环境必须通过环境变量提供独立的内部凭证。`.env.example` 只有占位符，不能提交真实密钥。

## 配置

Pydantic Settings 从 `.env` 和 `AI_` 前缀环境变量读取配置。关键配置包括：

| 变量 | 作用 | 默认值 |
| --- | --- | --- |
| `AI_PROVIDER_MODE` | `fake` 或 `openai-compatible` | `fake` |
| `AI_PROVIDER_BASE_URL` | OpenAI-compatible 服务地址 | `https://api.openai.com/v1` |
| `AI_PROVIDER_API_KEY` | 外部模型凭证 | 空 |
| `AI_MODEL` | 模型名称 | `gpt-4o-mini` |
| `AI_LLM_TIMEOUT_SECONDS` | 模型读取超时 | `15` |
| `AI_LLM_RETRY_COUNT` | 外部模型重试次数 | `1` |
| `AI_RAG_TOP_K` | 默认检索条数 | `2` |
| `AI_AGENT_MAX_TOOL_CALLS` | Agent 工具调用上限 | `3` |

修改后需要重启 Python 进程；本项目没有动态配置中心，也不假装支持热刷新。

## 能力边界

- Fake provider 是确定性的本地合同测试实现，不会修改工单。
- OpenAI-compatible provider 要求模型返回 JSON，随后由 Pydantic 校验枚举、长度和 `confidence` 范围；不能用自然语言包含判断代替 schema 校验。
- `ticket-analysis` 只返回分类、建议优先级、理由和置信度。建议不是业务决定。
- `ticket-reply-draft` 只返回人工审核草稿，不发送消息、不写入正式回复。
- Agent 只允许 `get_ticket_detail` 和 `get_ticket_history` 两个只读工具，工具参数经过 Pydantic 校验，并受最大调用次数限制。
- RAG 从 `knowledge/` 的小型客服知识库读取文档、切分段落、按词项重叠检索并返回来源元数据；`top_k` 是显式参数。
- MCP 使用官方 Python SDK 暴露 `search_ticket_knowledge` 只读工具：

```powershell
python -m app.services.mcp_server
```

Tool Calling 解决模型何时调用受控函数；MCP 演示的是工具与上下文的标准化发现/调用协议。MCP 模块与核心 Java 业务隔离，不给模型数据库权限。

## Java 边界

调用链是：

```text
Client → Java Spring Boot Security/Service → Python HTTP → AI advice
```

Java 只向 Python 发送已经授权的工单字段，并通过 `X-Internal-AI-Token` 保护内部请求。Python 需要读取工单或历史时，只能调用 Java 的受控只读 internal endpoint；它没有数据库账号，也不接受客户端 JWT 作为授权事实。

## 测试

```powershell
pytest
```

测试覆盖 health、内部令牌、结构化分析、回复草稿、provider invalid-output 映射、RAG top-k、Agent 工具边界和 MCP HTTP 合同。真实外部 LLM smoke test 只有在设置 `AI_PROVIDER_API_KEY` 后才执行；默认 fake provider 不需要凭证。

当前真实结果：`12 passed`。这些测试覆盖服务合同和关键边界，不代表生产环境压力测试或真实外部模型的成功率。

## Related Repositories

- [Java Core Backend](https://github.com/zc2777038647/ai-ticket-platform)：认证、授权、MySQL、Redis、工单状态和业务决策的可信边界。
- [Vue Demo Console](https://github.com/zc2777038647/ai-ticket-web)：本地浏览器和面试展示界面，浏览器只调用 Java API。

## Known Limitations

- 当前默认 provider 是确定性的 fake provider；真实 OpenAI-compatible LLM smoke test 只有在通过环境变量提供有效凭证时才执行。
- 本项目没有生产部署、压力测试或高并发性能结论，也没有数据库写权限。
- Python 配置修改需要重启进程；没有引入动态配置中心。

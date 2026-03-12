# 所有体现 MCP 协议的地方

## 1. 请求格式（JSON-RPC 2.0）

```python
{
    "jsonrpc": 2.0,       # ← MCP 基于 JSON-RPC 2.0 协议
    "id": 1,              # ← JSON-RPC 规定的请求 ID
    "method": "...",      # ← MCP 规定的方法名
    "params": {}          # ← JSON-RPC 规定的参数字段名
}
```

***

## 2. MCP 规定的方法名

```python
"method": "tools/list"   # ← 列出工具
"method": "tools/call"   # ← 调用工具
```

***

## 3. `tools/list` 的响应结构

MCP 规定服务器必须按这个格式返回：
```python
# 你的代码这样解析：
result["result"]["tools"]
# 对应服务器返回：
{
    "result": {
        "tools": [
            {
                "name": "search",
                "description": "...",
                "input_schema": {        # ← MCP 规定叫 input_schema（不是 parameters）
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        ]
    }
}
```

***

## 4. `tools/call` 的请求参数格式

```python
"params": {
    "name": tool_name,       # ← MCP 规定用 "name" 指定工具名
    "arguments": arguments   # ← MCP 规定用 "arguments" 传参（不是 params/inputs）
}
```

***

## 5. `tools/call` 的响应结构

```python
# 你在 execute() 里这样解析：
result["result"]["content"][0]["type"]   # ← "text"
result["result"]["content"][0]["text"]   # ← 实际内容
```

对应 MCP 规定的返回格式：
```json
{
    "result": {
        "content": [              
            {
                "type": "text",   # ← MCP 规定的 content 类型（还有 image、resource 等）
                "text": "结果内容"
            }
        ],
        "isError": false          # ← MCP 规定的错误标志（你代码里没用到）
    }
}
```

***

## 6. 请求头里的 Accept

```python
"Accept": "application/json, text/event-stream"
#                            ↑
#          MCP 支持两种传输方式：普通 JSON 和 SSE（Server-Sent Events 流式）
#          你的代码声明两种都接受
```

***

## 总结一张图

```
你的代码                        MCP 协议规定
─────────────────────────────────────────────
jsonrpc: 2.0              ←  基于 JSON-RPC 2.0
method: "tools/list"      ←  标准方法名
method: "tools/call"      ←  标准方法名
params.name               ←  工具名字段
params.arguments          ←  工具参数字段
result.content[].type     ←  响应内容类型
result.content[].text     ←  文本类型的响应
input_schema              ←  工具参数描述字段名
Accept: text/event-stream ←  支持 SSE 传输
```
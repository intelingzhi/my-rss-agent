from __future__ import annotations

import os
import json
from typing import Any

from .base import BaseTool


class SearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "使用搜索引擎获取最新信息。参数是一个查询字符串，返回搜索结果的摘要。"

    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询字符串",
                },
                 "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 5,
                },
            },
            "required": ["query"],
        }
    
    def execute(self, **kwargs: Any) -> tuple[bool, str]:
        """执行网络搜索"""

        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return False, json.dumps({"error": "TAVILY_KEY not found in environment"})
        
        client = TavilyClient(api_key=api_key)
        result = client.search(query, max_results=max_results)

        simplified_result = []

        for r in result.get("results", []):
            simplified_result.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:200],
            }
        )
            
        return False, json.dumps(simplified_result, ensure_ascii=False, indent=2)


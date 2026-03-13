from __future__ import annotations

import os
from typing import Any

import httpx

from .base import BaseTool

class WebFetchTool(BaseTool):
    """
    网页抓取工具
    用于从指定 URL 抓取网页内容。
    """

    @property
    def name(self) -> str:
        return "webfetch"

    @property
    def description(self) -> str:
        return "Fetch content from a URL. Use this to get the content of web pages when you need specific information from a website."


    def _parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum characters to return",
                    "default": 8000,
                },
            },
            "required": ["url"],
        }
    
    def execute(self, **kwargs) -> tuple[bool, str]:
        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 8000)

        if not url:
            return False, "Error: url is required"

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, follow_redirects=True)
                content = resp.text[:max_length]
                return False, content
        except Exception as e:
            return False, f"Error: {str(e)}"
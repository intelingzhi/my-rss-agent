# RAG 解决什么问题
## 为什么需要 RAG
没有 RAG 的 Agent：
- 只能基于训练数据回答
- 不知道你的公司文档、产品手册、会议记录
- 每次都是"盲猜"


## 有 RAG 的 Agent：

- 能从私有知识库中检索信息
- 基于真实文档回答问题
- 就像有了一个"第二大脑"

# RAG 本质
RAG = Retrieval-Augmented Generation（检索增强生成）。


核心思想很简单：
- 检索：从知识库中找到相关文档
- 增强：把找到的文档放进 prompt
- 生成：让 LLM 基于提供的文档回答

为什么不能直接把整个知识库提供给 LLM？
| 方案 | 问题 |
|------|------|
| 直接提供全部文档 | token 爆炸，费用爆炸 |
| 只提供相关文档 | 这就是 RAG 的核心思路 |


# 轻量级 RAG 选型
企业级 RAG 常用方案：

- 向量数据库：Milvus、Pinecone、Weaviate、FAISS
- embedding 模型：OpenAI Embedding、BGE、Sentence Transformers

我们的选择：
- FAISS：Facebook 开源的向量检索库，纯 Python/C++，无需额外服务
- Sentence Transformers：`all-MiniLM-L6-v2`，384 维向量，效果够用

为什么选这个组合：

1. FAISS：本地文件索引，零配置，易部署
2. Sentence Transformers：开源 embedding 模型，免费
3. 纯 Python：依赖少，易安装

> 一句话理解：RAG = 把文档切成小块 → 转成向量 → 存到向量数据库 → 检索时用向量相似度找相关文档。




# 什么是向量？
向量（Embedding）是 RAG 的核心。

一句话解释：把文字转换成一段数字，这段数字"理解"了文字的含义。
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# 输入文字
texts = ["苹果", "iPhone", "香蕉"]

# 输出向量（384 维数字）
vectors = model.encode(texts)
print(vectors.shape)  # (3, 384)
print(vectors[0][:10])  # 前10维: [0.12, -0.03, 0.08, ...]
```

向量的魔力：语义相近的文字，向量也"相近"。
```python

# 计算向量相似度
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

# 语义相近的句子
v1 = model.encode("苹果手机很好用")
v2 = model.encode("iPhone 使用体验不错")
v3 = model.encode("今天天气晴朗")

# 余弦相似度
from sklearn.metrics.pairwise import cosine_similarity
sim = cosine_similarity([v1], [v2, v3])
print(sim)
# [[0.89, 0.12]]  # v1 和 v2 相似度高，和 v3 很低
```
这就是 RAG 的原理：用向量相似度找到"语义相近"的文档。
| 概念 | 说明 |
|------|------|
| Embedding | 把文字转成向量的过程 |
| 向量维度 | "all-MiniLM-L6-v2" 是 384 维 |
| 相似度度量 | 余弦相似度（cosine similarity）、L2 距离、内积（IP） |
| 索引 | FAISS 用的是 IndexFlatIP（内积），配合归一化实现余弦相似度 |



# 2个方法
## `_build_index` — 构建知识库索引

**输入**：`documents` 文档列表，每项包含 `content`（文本内容）和 `source`（来源标识）

**流程**：

1. 检查文档列表是否为空，空则提前返回错误
2. 提取所有文档的 `content`，用 `sentence-transformers` 模型批量编码成向量矩阵
3. 转为 `float32` 类型（FAISS 要求）
4. 如果索引不存在，创建 `IndexFlatIP`（内积相似度索引）
5. 对所有向量做 L2 归一化（使内积等价于余弦相似度）
6. 将向量批量写入 FAISS 索引
7. 将每篇文档的元信息（id、content、source）追加到 `self.metadata` 列表
8. 调用 `_save()` 将索引和元数据持久化到磁盘

**输出**：`(False, "Indexed N documents")`

**特点**：支持增量构建，多次调用会追加而不是覆盖。

***

## `_query` — 查询知识库

**输入**：`question` 自然语言问题字符串

**流程**：

1. 检查问题是否为空、索引是否已构建，否则提前返回错误
2. 将问题编码成向量，同样转 `float32` + L2 归一化（与构建时保持一致）
3. 取 `k = min(3, 索引总数)`，避免文档数不足 3 条时报错
4. 调用 `index.search()` 返回最相似的 k 个文档的距离和下标
5. 用下标从 `self.metadata` 取出对应文档的 content 和 source
6. 过滤掉无效结果（`idx < 0`），拼接成带来源和相似度分数的上下文字符串
7. 返回上下文，**交给 LLM 生成最终答案**（RAG 模式）

**输出**：`(False, "Relevant context:\n\n[source] (similarity: 0.xxxx)\n内容...")`

**特点**：工具本身只负责检索，不生成答案，答案由调用它的 LLM 


# 示例
以一个具体场景为例：**给 agent 喂了两篇文档，然后提问**。

## Step 1：调用 `_build_index`

```python
documents = [
    {"content": "React 是 Facebook 开发的前端框架，用于构建用户界面。", "source": "react-intro"},
    {"content": "React 使用虚拟 DOM 提升渲染性能。",                   "source": "react-vdom"},
    {"content": "Python 是一种解释型编程语言，广泛用于数据科学。",       "source": "python-intro"},
]
```

**内部发生了什么：**

```
texts = ["React 是 Facebook...", "React 使用虚拟 DOM...", "Python 是一种..."]
         ↓ model.encode()
vectors = [
  [0.12, -0.34, 0.87, ...],   # 1536 维，代表第1篇文档的语义
  [0.15, -0.31, 0.85, ...],   # 和第1篇很相近（都是讲 React）
  [-0.45, 0.62, -0.21, ...],  # 和前两篇差距大（讲 Python）
]
         ↓ L2 归一化 + faiss.index.add()
         ↓ metadata 追加：
[
  {"id": 0, "content": "React 是 Facebook...", "source": "react-intro"},
  {"id": 1, "content": "React 使用虚拟 DOM...", "source": "react-vdom"},
  {"id": 2, "content": "Python 是一种...",      "source": "python-intro"},
]
```

***

## Step 2：调用 `_query`

```python
question = "React 是什么？"
```

**内部发生了什么：**

```
question_vector = model.encode(["React 是什么？"])
# → [0.13, -0.33, 0.86, ...]  ← 语义上接近 React 相关文档

index.search(question_vector, k=3)
# distances = [[0.97, 0.94, 0.41]]   ← 相似度分数
# indices   = [[0,    1,    2   ]]   ← 对应文档下标
```

**返回的 context：**

```
Relevant context:

[react-intro] (similarity: 0.9700)
React 是 Facebook 开发的前端框架，用于构建用户界面。

---

[react-vdom] (similarity: 0.9400)
React 使用虚拟 DOM 提升渲染性能。

---

[python-intro] (similarity: 0.4100)
Python 是一种解释型编程语言，广泛用于数据科学。
```

***

## Step 3：LLM 拿到 context 生成答案

agent 把上面的 context 塞进 messages，LLM 看到后回答：

```
根据知识库：
React 是 Facebook 开发的前端框架，主要用于构建用户界面，
它通过虚拟 DOM 技术来提升渲染性能。
```

**关键点**：LLM 的答案来自你喂进去的文档，而不是它自身的训练数据——这就是 RAG 的核心价值。
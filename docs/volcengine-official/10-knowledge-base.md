# 10 知识库 (VikingDB RAG)

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Knowledgebaseoverview?lang=zh
> 集成：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Integratingknowledgebaseinagent?lang=zh
> SDK：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Knowledge?lang=zh

## 概念

知识库基于 **VikingDB 向量库**实现百亿级存储、毫秒级检索，提供"文档管理—语义检索—智能对话"一体化 RAG 服务，支持结构化/非结构化多模态，适用于法律、教育、企业文档等。

## 流程

1. 在 VikingDB 控制台创建知识库（如 customer_support），上传文档（如 qa.md）。
2. 在 [PRODUCT] 知识库控制台**导入**该 VikingDB 知识库 → 查看 → 复制"集成代码"中的环境变量。
3. 在 Runtime"关联组件"中选择知识库；或代码中用 `KnowledgeBase(backend="viking", index=collection_name)`。

## SDK 集成示例

```python
from [BASE-ADK] import Agent, Runner
from [BASE-ADK].knowledgebase import KnowledgeBase
from [PRODUCT].apps import [PRODUCT]SimpleApp
app = [PRODUCT]SimpleApp()
knowledgebase = KnowledgeBase(backend="viking", index=os.getenv("DATABASE_VIKING_COLLECTION"))
agent = Agent(instruction="Answer customer's questions according to your knowledgebase.",
              model_name="doubao-seed-1-6-250615", knowledgebase=knowledgebase)
runner = Runner(agent=agent)
```
[PRODUCT].yaml：`DATABASE_VIKING_COLLECTION: <viking collection name>`。
调用：`[PRODUCT] invoke "你们有什么产品？"` → Agent 自动检索知识库并组织回答。

## 其他能力
- 知识检索、知识问答、查看原始文档、查看切片详情、配置私网访问、删除知识库。
- 2026-06-19 起支持对知识库文档的细粒度访问控制。

## 知识库 API
AddKnowledgeBase / UpdateKnowledgeBase / DeleteKnowledgeBase / GetKnowledgeBase / GetKnowledgeConnectionInfo / ListKnowledgeBases。

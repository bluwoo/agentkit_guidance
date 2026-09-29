#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mark pages actually read with substantive content."""
import json, os
here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, "read_status.json")
status = json.load(open(p, encoding="utf-8"))

BASE = "https://<INTERNAL_HOST>.com"
# URLs actually read with substantive content (2026-09-18)
read_urls = [
 "/docs/[PRODUCT]/Whatis[PRODUCT]?lang=zh",
 "/docs/[PRODUCT]/Productfeatures-18?lang=zh",
 "/docs/[PRODUCT]/Limits-7?lang=zh",
 "/docs/[PRODUCT]/SkillsOverview?lang=zh",
 "/docs/[PRODUCT]/Gatewayoverview?lang=zh",
 "/docs/[PRODUCT]/Knowledgebaseoverview?lang=zh",
 "/docs/[PRODUCT]/Memoryoverview?lang=zh",
 "/docs/[PRODUCT]/Sessionsoverview?lang=zh",
 "/docs/[PRODUCT]/A2ACenteroverview?lang=zh",
 "/docs/[PRODUCT]/Guardrailsoverview?lang=zh",
 "/docs/[PRODUCT]/Observabilityoverview-2?lang=zh",
 "/docs/[PRODUCT]/overview-of-evaluation-tools?lang=zh",
 "/docs/[PRODUCT]/Identityandpermission?lang=zh",
 "/docs/[PRODUCT]/SDKoverview-9?lang=zh",
 "/docs/[PRODUCT]/[BASE-ADK]overview?lang=zh",
 "/docs/[PRODUCT]/Tooloverview?lang=zh",
 "/docs/[PRODUCT]/Applicablescenarios-8?lang=zh",
 "/docs/[PRODUCT]/threelayer-memory-architecture-of-ai-dialogue-system-session-division-of-labor-and-coordination-of-s?lang=zh",
 "/docs/[PRODUCT]/Howmemoryworks?lang=zh",
 "/docs/[PRODUCT]/Gettingstarted1-minuteagentrapiddeployment?lang=zh",
 "/docs/[PRODUCT]/Quickstart?lang=zh",
 "/docs/[PRODUCT]/gateway_mode_and_mcp_request_counting_rules?lang=zh",
 "/docs/[PRODUCT]/connect-existing-rest-api-or-openapi-to-mcp-tool?lang=zh",
 "/docs/[PRODUCT]/connect-existing-mcp-server-to-[PRODUCT]-gateway?lang=zh",
 "/docs/[PRODUCT]/MCPprotocolversioncompatibilityinstructions?lang=zh",
 "/docs/[PRODUCT]/IntegratingMCPinagents?lang=zh",
 "/docs/[PRODUCT]/Integratingknowledgebaseinagent?lang=zh",
 "/docs/[PRODUCT]/Integratingmemoriesinagent?lang=zh",
 "/docs/[PRODUCT]/IntegratingSkillsintoagent?lang=zh",
 "/docs/[PRODUCT]/IntegratingGuardrailsinagents?lang=zh",
 "/docs/[PRODUCT]/Observability?lang=zh",
 "/docs/[PRODUCT]/BasicTroubleshootingUnifiedTroubleshootingSchemeBasedonObservationSystem?lang=zh",
 "/docs/[PRODUCT]/quick-access-a2a-center?lang=zh",
 "/docs/[PRODUCT]/outbound-authorization-agent-represents-the-user-to-access-volcano-engine-resources?lang=zh",
 "/docs/[PRODUCT]/Creatingruntimesconsole?lang=zh",
 "/docs/[PRODUCT]/Samplecallsfortextprompts?lang=zh",
 "/docs/[PRODUCT]/Runtime?lang=zh",
 "/docs/[PRODUCT]/Tools-2?lang=zh",
 "/docs/[PRODUCT]/Memory?lang=zh",
 "/docs/[PRODUCT]/Knowledge?lang=zh",
 "/docs/[PRODUCT]/mcp?lang=zh",
 "/docs/[PRODUCT]/Billinginstructions?lang=zh",
 "/docs/[PRODUCT]/Availableregions?lang=zh",
 "/docs/[PRODUCT]/[BASE-ADK]releasenotes?lang=zh",
 "/docs/[PRODUCT]/Newfeaturereleasenotes-30?lang=zh",
 "/docs/[PRODUCT]/Relatedcloudproduct-2?lang=zh",
 "/docs/[PRODUCT]/Tooltypes?lang=zh",
 "/docs/[PRODUCT]/[PRODUCT]-supportedinterfaces?lang=zh",
]
for u in read_urls:
    status[BASE + u] = "已读"
# empty / failed
status["https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Agentruntimeoverview?lang=zh"] = "失败"  # oversized image, no body
status["https://<INTERNAL_HOST>.com/docs/[PRODUCT]/A2AAgentJSONfileexample?lang=zh"] = "失败"  # redirects to release notes
status["https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPServiceAPIfile-specificationandexamples?lang=zh"] = "失败"
json.dump(status, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("marked", len(read_urls), "read, total status keys:", len(status))

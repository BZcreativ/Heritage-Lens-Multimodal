# Heritage Lens - Comprehensive Test Plan

**Objective:** Verify OpenClaw integration and all multimodal features work correctly.

---

## 1. OpenClaw Configuration Tests

### 1.1 Config File Validation
```bash
# Verify JSON syntax
python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null && echo "✅ Valid JSON"

# Check all skills are registered
grep -E '"heritage-(query|status|index|images|verify|config|demo|setup|slack-files|api|ui)"' ~/.openclaw/openclaw.json
```

### 1.2 Agent Configuration
```bash
# Verify agent directory structure
ls -la ~/.openclaw/agents/heritage-lens-multimodal/agent/

# Check bootstrap.md exists and has content
cat ~/.openclaw/agents/heritage-lens-multimodal/agent/bootstrap.md | head -20
```

**Expected Results:**
- [ ] openclaw.json is valid JSON
- [ ] All 11 skills are registered in the skills array
- [ ] Agent directory has all persona files (AGENTS.md, SOUL.md, etc.)
- [ ] bootstrap.md contains CRITICAL INSTRUCTIONS for Slack file handling

---

## 2. Skill Tests

### 2.1 Skill: heritage-query
```bash
# Test command exists in skill
cat ~/.openclaw/skills/heritage-query/SKILL.md | grep -A5 "/heritage-query"

# Test query execution (if OpenClaw running)
# /heritage-query "What are Olmec colossal heads?"
```

**Expected:** Skill file exists with proper usage instructions

### 2.2 Skill: heritage-status
```bash
cat ~/.openclaw/skills/heritage-status/SKILL.md | grep "/heritage-status"
```

### 2.3 Skill: heritage-index
```bash
cat ~/.openclaw/skills/heritage-index/SKILL.md | grep "/heritage-index"
```

### 2.4 Skill: heritage-images
```bash
cat ~/.openclaw/skills/heritage-images/SKILL.md | grep "/heritage-images"
```

### 2.5 Skill: heritage-slack-files
```bash
cat ~/.openclaw/skills/heritage-slack-files/SKILL.md | grep "/heritage-slack-files"

# Verify the skill references the Python tool
grep -q "slack_file_handler.py" ~/.openclaw/skills/heritage-slack-files/SKILL.md && echo "✅ References tool"
```

### 2.6 Skill: heritage-api
```bash
cat ~/.openclaw/skills/heritage-api/SKILL.md | grep "/heritage-api"

# Verify endpoints documented
grep -q "/health" ~/.openclaw/skills/heritage-api/SKILL.md && echo "✅ Health endpoint documented"
grep -q "/query" ~/.openclaw/skills/heritage-api/SKILL.md && echo "✅ Query endpoint documented"
```

### 2.7 Skill: heritage-ui
```bash
cat ~/.openclaw/skills/heritage-ui/SKILL.md | grep "/heritage-ui"

# Verify UI options documented
grep -q "streamlit" ~/.openclaw/skills/heritage-ui/SKILL.md && echo "✅ Streamlit documented"
grep -q "gradio" ~/.openclaw/skills/heritage-ui/SKILL.md && echo "✅ Gradio documented"
```

---

## 3. Python Backend Tests

### 3.1 Vision Module Tests
```bash
cd ~/heritage-lens-multimodal
source venv/bin/activate

# Test optional vision imports
python3 -c "
from modules.vision.optional_vision import OptionalVisionService
service = OptionalVisionService()
print(f'Vision enabled: {service.enabled}')
print(f'Available: {service.is_available()}')
"
```

**Expected:** Service initializes without errors, reports availability status

### 3.2 Slack File Handler Tests
```bash
# Test tool can be imported
python3 -c "
from tools.slack_file_handler import SlackFileHandler
handler = SlackFileHandler()
print(f'Handler initialized: {type(handler)}')
"
```

**Expected:** Imports successfully

### 3.3 API Server Tests
```bash
# Test API server starts
cd ~/heritage-lens-multimodal
python3 -c "
from api.heritage_api import app
print('FastAPI app loaded successfully')
"

# Start server in background
python3 api/heritage_api.py &
API_PID=$!
sleep 3

# Test health endpoint
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ API health check passes"

# Kill server
kill $API_PID 2>/dev/null
```

---

## 4. Slack Integration Tests

### 4.1 Slack File Download Test
**Prerequisites:** OpenClaw gateway running, Slack bot configured

```bash
# Upload a test PDF to Slack
# In Slack DM with Heritage Lens bot, upload test_olmec.pdf

# Expected bot behavior:
# 1. Bot receives file_shared event
# 2. Bot uses /heritage-slack-files skill
# 3. Bot downloads file using tools/slack_file_handler.py
# 4. Bot indexes file using /heritage-index skill
# 5. Bot confirms: "✅ Indexed test_olmec.pdf"
```

**Critical Test:** Bot must NOT say "I don't have direct access to download files"

### 4.2 Query with Slack Context
```bash
# After file is indexed, query:
# "What information is in the PDF I just uploaded?"

# Expected:
# - Bot retrieves content from indexed PDF
# - Provides 3-layer output
# - References correct source
```

---

## 5. Multimodal Feature Tests

### 5.1 Image Indexing
```bash
# Test image extraction from PDF
cd ~/heritage-lens-multimodal
python3 scripts/index_images.py --pdf data/corpus/test.pdf --dry-run

# Expected: Script runs without errors, reports extraction stats
```

### 5.2 CLIP Embeddings
```bash
# Test CLIP model loads and generates embeddings
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('clip-ViT-B-32')
print('CLIP model loaded')

import numpy as np
text_embedding = model.encode('ancient artifact')
print(f'Text embedding shape: {text_embedding.shape}')
"
```

### 5.3 Page-Aware Matching
```bash
# Test page-aware matching logic
python3 -c "
from agents.retrieval.multimodal_retrieval_agent import MultimodalRetrievalAgent
# Test the _page_aware_matching method with mock data
print('Page-aware matching available')
"
```

---

## 6. Backward Compatibility Tests

### 6.1 Text-Only Mode
```bash
# Disable multimodal in config
cd ~/heritage-lens-multimodal
python3 -c "
import yaml
with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)
config['multimodal']['enabled'] = False
with open('config/settings.yaml', 'w') as f:
    yaml.dump(config, f)
print('Multimodal disabled')
"

# Run test
python3 tests/test_backward_compatibility.py

# Re-enable
python3 scripts/migrate_to_multimodal.py
```

**Expected:** All 5 backward compatibility tests pass

---

## 7. Integration Test Checklist

### 7.1 OpenClaw Gateway
- [ ] Gateway starts without errors: `openclaw gateway start`
- [ ] Gateway recognizes all 11 skills
- [ ] Agent loads with correct persona files
- [ ] No config validation errors

### 7.2 Slack Integration
- [ ] Bot responds to @mentions
- [ ] Bot can receive file uploads
- [ ] Bot downloads files successfully
- [ ] Bot indexes downloaded files
- [ ] Bot queries indexed content

### 7.3 API Server
- [ ] Server starts on port 8000
- [ ] Health endpoint returns 200
- [ ] Query endpoint accepts POST requests
- [ ] Search endpoints return results

### 7.4 UI Components
- [ ] Streamlit app loads: `streamlit run ui/app.py`
- [ ] Gradio app loads: `python ui/gradio_app.py`
- [ ] UI displays 3-layer output correctly
- [ ] UI shows images when available

---

## 8. Manual End-to-End Test

### Test Scenario 1: Basic Query
1. Start OpenClaw gateway
2. Send query: "What are Olmec colossal heads?"
3. **Verify:** 3-layer output with L1 (Answer), L2 (Sources), L3 (Epistemic)

### Test Scenario 2: File Upload + Query
1. Upload PDF to Slack
2. Wait for indexing confirmation
3. Query: "Summarize the PDF I just uploaded"
4. **Verify:** Answer references uploaded PDF

### Test Scenario 3: Multimodal Query
1. Ensure images are indexed in Qdrant
2. Query: "Show me images of stone sculptures"
3. **Verify:** Answer includes image references

### Test Scenario 4: API Access
1. Start API server: `python api/heritage_api.py`
2. Query: `curl -X POST http://localhost:8000/query -d '{"query":"test"}'`
3. **Verify:** JSON response with 3-layer output

---

## 9. Troubleshooting Guide

### Issue: Skill not recognized
```bash
# Check skill is in openclaw.json
grep "heritage-<skill>" ~/.openclaw/openclaw.json

# Verify SKILL.md exists
ls ~/.openclaw/skills/heritage-<skill>/SKILL.md

# Restart gateway
openclaw gateway restart
```

### Issue: Slack file download fails
```bash
# Check tool exists
ls -la ~/heritage-lens-multimodal/tools/slack_file_handler.py

# Verify bootstrap.md has instructions
grep -A5 "DO NOT say you can't access files" \
  ~/.openclaw/agents/heritage-lens-multimodal/agent/bootstrap.md
```

### Issue: API server won't start
```bash
# Check port availability
lsof -i :8000

# Check dependencies
pip list | grep -E "fastapi|uvicorn"

# Test imports
python3 -c "from api.heritage_api import app"
```

---

## 10. Sign-off

**Tester:** _______________  **Date:** _______________

| Component | Status | Notes |
|-----------|--------|-------|
| OpenClaw Config | [ ] Pass [ ] Fail | |
| All 11 Skills | [ ] Pass [ ] Fail | |
| Slack File Download | [ ] Pass [ ] Fail | |
| 3-Layer Output | [ ] Pass [ ] Fail | |
| API Endpoints | [ ] Pass [ ] Fail | |
| UI Launch | [ ] Pass [ ] Fail | |
| Backward Compatibility | [ ] Pass [ ] Fail | |

**Overall Result:** [ ] ALL TESTS PASS [ ] ISSUES FOUND

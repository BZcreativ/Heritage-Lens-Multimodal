# Heritage Lens Multimodal - System Status Monitoring

## Health Check Points

### Component Status

#### Core Components (Required)

| Component | Status | Last Check | Notes |
|-----------|--------|------------|-------|
| Qdrant Connection | ✅ | Auto | Vector store for text |
| LLM API | ✅ | Auto | OpenRouter/OpenAI configured |
| Text Retrieval | ✅ | Auto | LlamaIndex initialized |
| Synthesis Agent | ✅ | Auto | Ready for queries |
| Epistemic Agent | ✅ | Auto | Bias analysis ready |
| Critic Agent | ✅ | Auto | Quality evaluation ready |

#### Optional Components (Enhanced Features)

| Component | Status | Last Check | Notes |
|-----------|--------|------------|-------|
| Vision Service | ⚠️ | Auto | Dependencies optional |
| CLIP Model | ⚠️ | Auto | sentence-transformers |
| Image Collection | ⚠️ | Auto | Requires indexing |
| GLM-4V API | ⚠️ | Auto | Z.ai integration |

## Operational Modes

### Current Mode: `FULL_MULTIMODAL` or `TEXT_ONLY`

Determined by:
- `multimodal.enabled` in config
- Vision dependencies availability
- Image collection population

### Mode Detection

```python
if vision_service.is_available() and images_indexed > 0:
    mode = "FULL_MULTIMODAL"
elif vision_service.is_available():
    mode = "VISION_READY_NO_IMAGES"
else:
    mode = "TEXT_ONLY"
```

## System Statistics

### Current Metrics

- **Sessions Active**: [Dynamic]
- **Images Indexed**: [Dynamic]
- **Text Documents**: [Dynamic]
- **Avg Query Time**: [Dynamic]
- **Revision Rate**: [Dynamic]

### Performance Thresholds

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Query Latency | <2s | 2-5s | >5s |
| Error Rate | <1% | 1-5% | >5% |
| Revision Rate | <10% | 10-30% | >30% |
| Qdrant Response | <100ms | 100-500ms | >500ms |

## Error Monitoring

### Tracked Errors

1. **VisionServiceUnavailable**
   - Severity: Warning
   - Action: Fall back to text-only
   - Alert: Log only

2. **QdrantConnectionError**
   - Severity: Critical
   - Action: Queue queries, notify user
   - Alert: Immediate

3. **LLM API Error**
   - Severity: High
   - Action: Retry with backoff
   - Alert: After 3 failures

4. **Image Encoding Error**
   - Severity: Warning
   - Action: Skip image, continue
   - Alert: Log only

### Error Recovery

#### Automatic Retries
- LLM calls: 3 retries with exponential backoff
- Qdrant queries: 2 retries
- Image encoding: 1 retry

#### Graceful Degradation
1. Vision fails → Text-only mode
2. Qdrant fails → Return error with context
3. LLM fails → Return partial results
4. Critic fails → Accept output with warning

## Session Health

### Per-Session Monitoring

- Query count
- Average response time
- Error count
- Revision count
- Last activity timestamp

### Session Cleanup

- Auto-cleanup after 30 minutes inactive
- Max 100 sessions stored
- Oldest sessions evicted first

## Dependency Status

### Required Dependencies ✅

```
llama-index>=0.10.0
qdrant-client>=1.7.0
openai>=1.0.0
pyyaml>=6.0
```

### Optional Dependencies ⚠️

```
sentence-transformers>=2.2.0  # For vision
Pillow>=10.0.0                # For image processing
PyMuPDF>=1.23.0              # For PDF extraction
```

### Missing Optional Dependencies

When optional dependencies are missing:
- Log warning at startup
- Disable vision features
- Continue with core functionality
- Document in status output

## API Status

### OpenRouter API
- Endpoint: https://openrouter.ai/api/v1
- Status: Monitored per-request
- Fallback: Direct OpenAI if configured

### Qdrant API
- Endpoint: http://localhost:6333
- Status: Health check on startup
- Retry: 3 attempts before marking unavailable

### GLM-4V API (Optional)
- Endpoint: https://api.z.ai
- Status: Checked if API key present
- Fallback: CLIP-only vision if unavailable

## Self-Healing Actions

### Automatic Recovery

1. **Temporary LLM Failure**
   - Retry with exponential backoff
   - Switch to fallback model if configured
   - Degrade to shorter responses

2. **Qdrant Reconnection**
   - Detect disconnection
   - Attempt reconnection every 10s
   - Queue queries during outage

3. **Vision Service Recovery**
   - Detect import failures at startup
   - Retry initialization on demand
   - Clear cache if corruption detected

### Manual Intervention Required

1. **Configuration Errors**
   - Invalid API keys
   - Missing required settings
   - Incompatible version combinations

2. **Data Corruption**
   - Corrupted vector store
   - Invalid embeddings
   - Missing metadata

## Alert Thresholds

### Immediate Alerts
- Qdrant connection lost
- LLM API completely unavailable
- Critical error rate >10%

### Daily Summaries
- Total queries processed
- Error rates by category
- Performance metrics
- Resource utilization

### Weekly Reports
- Usage patterns
- Component health trends
- Capacity planning needs
- Feature utilization

## Status Commands

### For Users

```
/health - Show system status
/stats - Show usage statistics
/mode - Show current operational mode
```

### For Administrators

```bash
# Check system health
python verify_setup.py

# Check component status
python -c "from agents.orchestrator import EnhancedOrchestrator; o = EnhancedOrchestrator(); print(o.get_stats())"

# View logs
tail -f logs/heritage_lens.log

# Check Qdrant
curl http://localhost:6333/healthz
```

## Maintenance Windows

### Scheduled Maintenance

- Vector store optimization: Weekly
- Log rotation: Daily
- Cache cleanup: On startup
- Session purge: Every 30 min

### Unscheduled Maintenance

- Dependency updates: As needed
- Configuration reload: On change
- Emergency restart: Critical errors only

## Incident Response

### Severity Levels

1. **Critical**: System completely unavailable
   - Response: Immediate investigation
   - Communication: Broadcast to all users

2. **High**: Core functionality impaired
   - Response: <1 hour investigation
   - Communication: Status page update

3. **Medium**: Optional features unavailable
   - Response: <4 hour investigation
   - Communication: Logged only

4. **Low**: Performance degradation
   - Response: Next business day
   - Communication: Weekly report

### Rollback Procedures

1. Configuration issues:
   ```bash
   cp config/settings.yaml.backup.* config/settings.yaml
   ```

2. Dependency issues:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. Data issues:
   ```bash
   # Reindex from source documents
   python -m pipelines.pdf_extraction.multimodal_ingest data/corpus/
   ```

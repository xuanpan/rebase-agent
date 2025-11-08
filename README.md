# Rebase Agent - AI Intelligence Layer

The AI-powered backend for business-focused transformation analysis. Part of the Rebase ecosystem for legacy system modernization and code transformation.

## Overview

Rebase Agent provides intelligent automation for transformation workflows through:

- **Chat-First Interface**: Natural conversation-driven discovery
- **Domain-Driven Architecture**: Extensible transformation types
- **Business Value Focus**: ROI-driven analysis and recommendations
- **Universal Workflow**: Discover → Assess → Justify → Plan

## Supported Transformations

- **Legacy Modernization**: Comprehensive system overhauls
- **Framework Migration**: React→Vue, Django→FastAPI, etc.
- **Language Conversion**: Python→Go, JavaScript→TypeScript
- **Performance Optimization**: Database tuning, caching strategies
- **Architecture Redesign**: Monolith→Microservices, cloud-native
- **Dependency Upgrade**: Security patches, version updates

## Quick Start

```bash
# Clone and setup
git clone https://github.com/xuanpan/rebase-agent
cd rebase-agent
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn app.main:app --reload
```

## API Usage

### Start a Transformation Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/chat/start" \
  -H "Content-Type: application/json" \
  -d '{"initial_message": "We want to migrate from React to Vue"}'
```

### Continue the Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "message": "We have 5 developers and complex state management issues"
  }'
```

### Get Business Case

```bash
curl "http://localhost:8000/api/v1/chat/sessions/session-123/summary"
```

## Architecture

```
core/                    # Universal AI infrastructure
├── conversation/        # Chat-first conversation management
├── question_engine.py   # Dynamic question generation
└── transformation_engine.py  # 4-phase workflow orchestrator

domains/                 # Transformation-specific logic
├── framework_migration/ # React→Vue, Angular→Svelte
├── language_conversion/ # Python→Go, JS→TypeScript
├── performance_optimization/
└── architecture_redesign/

app/                     # FastAPI application
├── api/v1/chat.py      # Conversational endpoints
└── models/             # Pydantic models
```

## Integration

Part of the **Rebase Ecosystem**:
- **rebase-kit**: Technical implementation tools
- **rebase-web**: Business stakeholder interface
- **rebase-agent**: AI analysis and ROI calculation (this repository)

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
flake8 .
mypy .

# Start with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
# REDIS_URL=redis://localhost:6379  # Not needed for POC
DATABASE_URL=postgresql://user:pass@localhost/rebaseagent
LOG_LEVEL=INFO
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
# Rebase Agent - AI Intelligence Layer

## Rebase Ecosystem Overview

The **Rebase Ecosystem** is a comprehensive business-focused legacy system modernization platform designed to transform legacy codebases through structured, ROI-driven workflows.

### Multi-Repository Architecture

**rebase-kit** - Foundation & CLI
- Core package with shared templates, schemas, and business logic
- Command-line interface for technical users (`rebase init`)
- Published to PyPI for use by other ecosystem components

**rebase-web** - Business User Interface  
- React/Next.js application for business stakeholders
- Guided workflows for discover and justify phases
- Executive dashboards and collaboration features

**rebase-agent** (This Repository) - AI Intelligence Layer
- Domain-driven FastAPI backend with extensible AI infrastructure
- Automated code analysis, ROI calculation, and decision support
- Core/domains architecture supporting all types of business-justified transformations

## Repository Overview

**This Repository**: `rebase-agent` (AI Intelligence Layer)
**Role**: FastAPI backend providing AI-powered automation for transformation workflows

## Domain-Driven Architecture

```
rebase-agent/                    # THIS REPOSITORY
├── core/                        # Generic AI infrastructure
│   ├── __init__.py
│   ├── context_manager.py      # Conversation context management
│   ├── llm_client.py           # LLM API wrapper (OpenAI, Claude, etc.)
│   ├── prompt_engine.py        # Template rendering & prompt management
│   ├── validator.py            # Output validation & schema checking
│   └── question_engine.py      # Dynamic questioning logic
│
├── domains/                     # Transformation domain logic
│   ├── __init__.py
│   ├── modernization/           # Legacy system modernization (comprehensive overhauls)
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Legacy system analysis & classification
│   │   ├── phases/             # Modernization-specific workflow
│   │   │   ├── __init__.py
│   │   │   ├── discover.py     # Business discovery automation
│   │   │   ├── assess.py       # Technical assessment AI
│   │   │   ├── justify.py      # ROI calculation engine
│   │   │   └── plan.py         # Implementation planning
│   │   ├── spec_generator.py   # Generates modernization specifications
│   │   ├── schema.py           # Data models & validation
│   │   └── prompts/            # Domain-specific prompt templates
│   │       ├── discovery/
│   │       ├── assessment/
│   │       ├── justification/
│   │       └── planning/
│   ├── framework_migration/     # Framework-to-framework transformations
│   │   ├── analyzer.py         # Framework analysis (React→Vue, etc.)
│   │   ├── roi_calculator.py   # Migration-specific ROI
│   │   └── migration_planner.py
│   ├── language_conversion/     # Language-to-language transformations  
│   │   ├── analyzer.py         # Language analysis (Python→Go, etc.)
│   │   ├── compatibility_checker.py
│   │   └── conversion_planner.py
│   ├── performance_optimization/ # Performance improvement transformations
│   │   ├── profiler.py         # Performance analysis
│   │   ├── bottleneck_detector.py
│   │   └── optimization_planner.py
│   ├── architecture_redesign/   # System architecture transformations
│   │   ├── pattern_analyzer.py # Monolith→Microservices, etc.
│   │   ├── scalability_assessor.py
│   │   └── architecture_planner.py
│   └── dependency_upgrade/      # Library/framework upgrade transformations
│       ├── security_analyzer.py # Vulnerability assessment
│       ├── compatibility_checker.py
│       └── upgrade_planner.py
│
├── app/                        # FastAPI application layer
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── modernization.py
│   │   │   ├── analysis.py
│   │   │   └── projects.py
│   │   └── dependencies.py     # Dependency injection
│   ├── middleware/             # Authentication, CORS, etc.
│   └── config.py              # Configuration management
│
├── integrations/               # External tool connectors
│   ├── __init__.py
│   ├── rebase_kit.py          # Import rebase-kit package
│   ├── code_analysis/         # Code quality tools
│   │   ├── sonarqube.py
│   │   ├── codeclimate.py
│   │   └── security_scanners.py
│   └── project_management/    # PM tools integration
│       ├── jira.py
│       └── github.py
│
├── tests/                      # Comprehensive test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── requirements.txt           # Dependencies including rebase-kit
├── pyproject.toml            # Project configuration
├── docker-compose.yml        # Local development environment
└── Dockerfile                # Container deployment
```

## Core AI Infrastructure

### LLM Client (`core/llm_client.py`)
**Purpose**: Unified interface for multiple LLM providers
**Features**:
- Support for OpenAI GPT-4, Claude, Gemini
- Automatic retry and rate limiting
- Cost tracking and usage analytics
- Response streaming for real-time UI
- Model selection based on task complexity

### Prompt Engine (`core/prompt_engine.py`)
**Purpose**: Template-based prompt management
**Features**:
- Jinja2 templating with modernization-specific filters
- Dynamic prompt composition based on context
- Version control for prompt templates
- A/B testing capabilities for prompt optimization
- Integration with rebase-kit templates

### Question Engine (`core/question_engine.py`)
**Purpose**: Dynamic questioning for incomplete information
**Features**:
- Context-aware question generation
- Follow-up question chaining
- Stakeholder-specific questioning patterns
- Integration with business workflow steps

### Context Manager (`core/context_manager.py`)
**Purpose**: Conversation and project context management
**Features**:
- Long-term conversation memory
- Project state persistence
- Cross-phase context continuity
- Stakeholder context switching

## Modernization Domain (`domains/modernization/`)

### Phase Automation

#### Discover Phase (`phases/discover.py`)
**Purpose**: Automate business discovery interviews and analysis
**Key Functions**:
- `conduct_stakeholder_interview()` - AI-driven stakeholder interviews
- `analyze_business_pain_points()` - Extract and categorize pain points
- `generate_success_criteria()` - Define measurable success metrics
- `calculate_opportunity_cost()` - Estimate cost of inaction

**API Endpoints**:
- `POST /api/v1/modernization/discover/start` - Initialize discovery
- `POST /api/v1/modernization/discover/interview` - Conduct interview
- `GET /api/v1/modernization/discover/summary` - Generate summary

#### Assess Phase (`phases/assess.py`)
**Purpose**: Automated technical assessment and risk analysis
**Key Functions**:
- `analyze_codebase_structure()` - Code organization analysis
- `identify_technical_debt()` - Technical debt quantification
- `assess_security_vulnerabilities()` - Security risk assessment
- `evaluate_performance_bottlenecks()` - Performance analysis

**API Endpoints**:
- `POST /api/v1/modernization/assess/analyze` - Start technical analysis
- `GET /api/v1/modernization/assess/risks` - Risk assessment report
- `GET /api/v1/modernization/assess/metrics` - Technical metrics

#### Justify Phase (`phases/justify.py`)
**Purpose**: ROI calculation and business case generation
**Key Functions**:
- `calculate_modernization_roi()` - ROI analysis with confidence intervals
- `estimate_migration_costs()` - Comprehensive cost estimation
- `analyze_risk_factors()` - Risk quantification and mitigation
- `generate_executive_summary()` - Business case documentation

**API Endpoints**:
- `POST /api/v1/modernization/justify/calculate` - ROI calculation
- `GET /api/v1/modernization/justify/business-case` - Business case
- `POST /api/v1/modernization/justify/scenarios` - What-if analysis

#### Plan Phase (`phases/plan.py`)
**Purpose**: Implementation strategy and roadmap generation
**Key Functions**:
- `generate_migration_strategy()` - Step-by-step migration plan
- `design_target_architecture()` - Modern architecture design
- `create_implementation_roadmap()` - Timeline and milestones
- `estimate_resource_requirements()` - Team and budget planning

**API Endpoints**:
- `POST /api/v1/modernization/plan/strategy` - Generate strategy
- `GET /api/v1/modernization/plan/roadmap` - Implementation roadmap
- `POST /api/v1/modernization/plan/validate` - Plan validation

### Code Analyzer (`analyzer.py`)
**Purpose**: Intelligent code analysis and classification
**Key Functions**:
- `detect_legacy_patterns()` - Identify legacy code patterns
- `classify_system_type()` - System categorization
- `extract_dependencies()` - Dependency mapping
- `analyze_coupling_cohesion()` - Code quality metrics

## Integration Layer (`integrations/`)

### Rebase Kit Integration (`rebase_kit.py`)
**Purpose**: Import and use rebase-kit templates and utilities
**Key Functions**:
- `load_templates()` - Import templates from rebase-kit
- `validate_schemas()` - Use rebase-kit validation
- `sync_project_state()` - Synchronize with CLI projects

### Code Analysis Tools (`code_analysis/`)
**Purpose**: Integration with external code quality tools
**Supported Tools**:
- SonarQube: Code quality and security analysis
- CodeClimate: Maintainability and technical debt
- Security scanners: SAST/DAST integration
- Performance profilers: APM tool integration

## API Design Principles

### RESTful Architecture
- Resource-based URLs (`/api/v1/projects/{id}/phases/discover`)
- HTTP methods for actions (GET, POST, PUT, DELETE)
- Standard HTTP status codes
- JSON request/response format

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API key management for integrations
- Rate limiting and quotas

### Async Processing
- Background job processing for long-running analysis
- WebSocket support for real-time updates
- Progress tracking for multi-step workflows
- Queue management for concurrent requests

## Development Guidelines

### Core Infrastructure Development
**Focus Areas**:
- **Reliability**: Robust error handling and graceful degradation
- **Scalability**: Async processing and horizontal scaling
- **Observability**: Comprehensive logging and metrics
- **Security**: Input validation and secure API design

### Domain Development
**Focus Areas**:
- **Business Logic**: Domain-specific expertise and workflows
- **Integration**: Seamless connection with external tools
- **Validation**: Business rule enforcement and data validation
- **Extensibility**: Plugin architecture for new capabilities

### Code Style & Patterns
- **FastAPI Patterns**: Dependency injection, async/await
- **Domain-Driven Design**: Clear separation of concerns
- **Type Hints**: Full typing for better IDE support
- **Error Handling**: Custom exceptions with detailed context
- **Testing**: Unit, integration, and end-to-end tests

## Business Context Integration

### Always Emphasize Business Value
- Connect technical metrics to business outcomes
- Include ROI considerations in all recommendations
- Reference decision gates throughout workflows
- Provide executive-friendly summaries

### Risk-First Approach
- Identify and quantify risks early
- Provide mitigation strategies
- Include confidence intervals in estimates
- Escalate high-risk scenarios appropriately

### Stakeholder-Centric Design
- Tailor outputs to specific stakeholder needs
- Support collaborative decision-making
- Enable approval workflows
- Maintain audit trails for governance

## Success Metrics

**API Performance**: Response times, throughput, error rates
**Analysis Quality**: Accuracy of technical assessments and ROI calculations
**Business Impact**: Success rate of modernization projects using the platform
**Developer Experience**: Ease of integration and extensibility
**Ecosystem Integration**: Seamless connection with rebase-kit and rebase-web

---

## Quick Reference for AI Assistants

**Repository Role**: AI intelligence layer for Rebase ecosystem
**Architecture**: Domain-driven FastAPI backend with core/domains separation
**Primary Users**: rebase-web frontend, CLI integrations, direct API consumers
**Key Domains**: Modernization, framework migration, language conversion, performance optimization, architecture redesign, dependency upgrade
**Core Value**: Automated AI-powered analysis and decision support for business-justified transformations
**Integration Points**: Imports rebase-kit, serves rebase-web, standalone API access
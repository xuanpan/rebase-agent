# Installation and Development Guide

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Test the chat interface**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/chat/start" \
     -H "Content-Type: application/json" \
     -d '{"message": "I want to migrate from React to Vue"}'
   ```

## Development Environment with Docker

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f rebase-agent
   ```

3. **Access the API**:
   - API: http://localhost:8000
   # - Redis: localhost:6379  # Not needed for POC
   - PostgreSQL: localhost:5432

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Next Steps

After installation, you can:
1. Test the chat interface with transformation questions
2. Explore the domain system by adding new transformation types
3. Integrate with the frontend (rebase-web)
4. Add custom prompt templates for specific use cases
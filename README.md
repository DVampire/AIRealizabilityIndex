---
title: AI Realizability Index
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "latest"
app_file: app.py
pinned: false
---

# AI Realizability Index - AI Paper Evaluation System

A comprehensive system for evaluating AI research papers using advanced language models with asynchronous processing and concurrent evaluation capabilities.

## Features

- **Daily Paper Crawling**: Automatically fetches papers from Hugging Face daily
- **AI Evaluation**: Uses Claude Sonnet to evaluate papers across multiple dimensions
- **Concurrent Processing**: True asynchronous evaluation with multiple papers processed simultaneously
- **Re-evaluation**: Ability to re-run evaluations for papers with updated results
- **Batch Evaluation**: "Evaluate All" feature to process multiple papers at once
- **Interactive Dashboard**: Beautiful web interface for browsing and evaluating papers
- **Asynchronous Database**: High-performance SQLite with WAL mode for concurrent operations
- **Smart Navigation**: Intelligent date navigation with fallback mechanisms
- **Real-time Status Updates**: Live progress tracking and notifications

## Recent Updates

### v0.1.0 - Asynchronous & Concurrent Features
- **Asynchronous Database**: Migrated from `sqlite3` to `aiosqlite` for better performance
- **Concurrent Evaluation**: Multiple papers can be evaluated simultaneously
- **Re-evaluation**: Added "Re-evaluate" button for papers to update evaluation results
- **Batch Processing**: "Evaluate All" button to process all un-evaluated papers
- **Enhanced UI**: Improved progress indicators and real-time notifications
- **Database Optimization**: WAL mode and performance pragmas for better concurrency

## Hugging Face Spaces Deployment

This application is configured for deployment on Hugging Face Spaces.

### Configuration

- **Port**: 7860 (Hugging Face Spaces standard)
- **Health Check**: `/api/health` endpoint
- **Docker**: Optimized Dockerfile for containerized deployment

### Deployment Steps

1. **Fork/Clone** this repository to your Hugging Face account
2. **Create a new Space** on Hugging Face
3. **Select Docker** as the SDK
4. **Set Environment Variables**:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access
5. **Deploy**: The Space will automatically build and deploy

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_api_key_here
PORT=7860  # Optional, defaults to 7860
```

## Local Development

### Prerequisites

- Python 3.9+
- Anthropic API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd paperindex
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the application**:
   - Main interface: http://localhost:7860
   - API documentation: http://localhost:7860/docs

## API Endpoints

### Core Endpoints

- `GET /api/daily` - Get daily papers with smart navigation
- `GET /api/paper/{paper_id}` - Get paper details
- `GET /api/eval/{paper_id}` - Get paper evaluation
- `GET /api/health` - Health check endpoint

### Evaluation Endpoints

- `POST /api/papers/evaluate/{arxiv_id}` - Start paper evaluation
- `POST /api/papers/reevaluate/{arxiv_id}` - Re-evaluate a paper
- `GET /api/papers/evaluate/{arxiv_id}/status` - Get evaluation status
- `GET /api/papers/evaluate/active-tasks` - Get currently running evaluations

### Cache Management

- `GET /api/cache/status` - Get cache statistics
- `POST /api/cache/clear` - Clear all cached data
- `POST /api/cache/refresh/{date}` - Refresh cache for specific date

## Architecture

### Frontend
- **HTML/CSS/JavaScript**: Modern, responsive interface
- **Real-time Updates**: Dynamic content loading with polling
- **Theme Support**: Light/dark mode toggle
- **Progress Indicators**: Visual feedback for evaluation status
- **Batch Operations**: "Evaluate All" functionality with sequential processing

### Backend
- **FastAPI**: High-performance web framework
- **Async SQLite**: `aiosqlite` with WAL mode for concurrent operations
- **Async Processing**: Background evaluation tasks with task tracking
- **Concurrent Evaluation**: Multiple papers evaluated simultaneously
- **Caching**: Intelligent caching system for performance

### AI Integration
- **Async Anthropic**: Non-blocking API calls with `AsyncAnthropic`
- **Multi-dimensional Analysis**: Comprehensive evaluation criteria
- **Structured Output**: JSON-based evaluation results
- **Error Handling**: Robust error handling and retry mechanisms

## Database Schema

### Papers Table
```sql
CREATE TABLE papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    abstract TEXT,
    categories TEXT,
    published_date TEXT,
    evaluation_content TEXT,
    evaluation_score REAL,
    overall_score REAL,
    evaluation_tags TEXT,
    evaluation_status TEXT DEFAULT 'not_started',
    is_evaluated BOOLEAN DEFAULT FALSE,
    evaluation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Database Optimizations
- **WAL Mode**: `PRAGMA journal_mode=WAL` for better concurrency
- **Performance Pragmas**: Optimized settings for concurrent access
- **Asynchronous Operations**: All database calls are async/await

## Evaluation Dimensions

The system evaluates papers across 12 key dimensions:

1. **Task Formalization** - Clarity of problem definition
2. **Data & Resource Availability** - Access to required data
3. **Input-Output Complexity** - Complexity of inputs/outputs
4. **Real-World Interaction** - Practical applicability
5. **Existing AI Coverage** - Current AI capabilities
6. **Automation Barriers** - Technical challenges
7. **Human Originality** - Creative contribution
8. **Safety & Ethics** - Responsible AI considerations
9. **Societal/Economic Impact** - Broader implications
10. **Technical Maturity Needed** - Development requirements
11. **3-Year Feasibility** - Short-term potential
12. **Overall Automatability** - Comprehensive assessment

## Key Features

### Concurrent Evaluation
- Multiple papers can be evaluated simultaneously
- Global task tracking prevents duplicate evaluations
- Real-time status updates via polling
- Automatic error handling and recovery

### Re-evaluation System
- "Re-evaluate" button appears after initial evaluation
- Updates existing evaluation results in database
- Maintains evaluation history and timestamps
- Same comprehensive evaluation criteria

### Batch Processing
- "Evaluate All" button processes all un-evaluated papers
- Sequential processing with delays to prevent API overload
- Progress tracking and real-time notifications
- Automatic button state management

### Enhanced UI/UX
- Progress circles with proper layering
- Bottom-right notification system
- Dynamic button states and text updates
- Responsive design with modern styling

## Performance Optimizations

### Database
- Asynchronous operations with `aiosqlite`
- WAL mode for better concurrency
- Optimized SQLite pragmas
- Connection pooling and management

### API Calls
- Non-blocking Anthropic API calls
- Concurrent evaluation processing
- Task tracking and management
- Error handling and retry logic

### Frontend
- Efficient DOM manipulation
- Polling with appropriate intervals
- Memory management for log entries
- Optimized event handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.



# Project Overview

iptv-sniffer is a lightweight Python tool for discovering and validating IPTV channels on local networks. It provides M3U playlist import/export capabilities, stream validation via FFmpeg, and a web interface for user interaction.

**Repository Description**: A lightweight tool to sniff available IPTV channels on your network, with M3U import, export, and management support.

**Reference Implementation**: Inspired by [thsrite/iptv-sniff](https://github.com/thsrite/iptv-sniff), but using `ffmpeg-python` library instead of command-line string concatenation for better type safety and maintainability.

Agents and contributors should focus on network scanning ethics, FFmpeg integration best practices, M3U format compliance, and Docker deployment patterns.

## Goals for AI Agents

When generating or modifying code, agents should aim to:

- Write idiomatic Python code with type hints and Pydantic models (never use `dataclass` for data validation)
- Use `ffmpeg-python` library instead of subprocess command-line strings for FFmpeg operations
- Implement asynchronous network scanning with proper rate limiting to avoid network abuse
- Follow TDD: write pytest-based tests before implementing features
- Build modular, testable components: network scanning, stream validation, M3U parsing, web API
- Provide clear logging with structured context (channel URL, scan duration, validation status)
- Respect Docker best practices: multi-stage builds, small images, health checks
- Ensure web interface is responsive and user-friendly

## Project Structure & Key Modules

```bash
iptv-sniffer/
  iptv_sniffer/
    cli/
        app.py           # CLI entry point (Click/Typer)
        scan.py          # Network scanning commands
        validate.py      # Stream validation commands
        export.py        # M3U export commands
    web/
        app.py           # Flask/FastAPI application
        api/
            channels.py  # Channel management endpoints
            scan.py      # Scanning trigger endpoints
            export.py    # M3U export endpoints
        static/          # Static assets (HTML, CSS, JS)
            index.html   # Main web interface
    scanner/
        discovery.py     # Network discovery (UDP multicast, HTTP probing)
        validator.py     # Stream validation using ffmpeg-python
        rate_limiter.py  # Rate limiting for network requests
    m3u/
        parser.py        # M3U/M3U8 parser
        generator.py     # M3U/M3U8 generator
        models.py        # M3U data models (Pydantic)
    channel/
        models.py        # Channel data models (Pydantic)
        repository.py    # Channel CRUD operations
        deduplicator.py  # Channel deduplication logic
    storage/
        file_storage.py  # JSON/M3U file persistence
        db_storage.py    # Optional: SQLite persistence
    utils/
        log.py           # Logging helpers
        config.py        # Configuration management
        ffmpeg.py        # FFmpeg wrapper utilities
  tests/
    unit/                # Unit tests (one test file per source file)
    integration/         # Integration tests (Docker, FFmpeg, web API)
    fixtures/
        sample.m3u       # Sample M3U files for testing
        invalid.m3u      # Invalid M3U for error testing
  Dockerfile
  docker-compose.yml
  requirements.txt
  pyproject.toml
  AGENTS.md
  README.md
```

## Tools & Conventions

- **Project management**: `uv` (recommended) or `poetry` for dependency management and lockfiles
- **Type checking**: `mypy` with strict mode; ensure ffmpeg-python stubs are installed
- **Linting**: `ruff` configured to enforce no `Any` in public signatures (ANN401)
- **Testing**: `pytest` + `pytest-asyncio` (if using async); each feature must include unit tests
- **Network scanning**: Use `asyncio` + `aiohttp` for concurrent HTTP requests; limit concurrency to avoid network abuse
- **FFmpeg integration**: Use `ffmpeg-python` library, never subprocess with command strings
  - Example: `ffmpeg.input(url, **options).output('pipe:', format='null').run(capture_stderr=True)`
  - Always set timeouts for stream probing (default: 10 seconds)
  - Catch `ffmpeg.Error` exceptions and log stderr output
- **Web framework**: Flask (simple, blocking) or FastAPI (async, type-safe)
  - If Flask: use threading for background tasks, serve static files via `send_from_directory`
  - If FastAPI: use async routes, background tasks via `BackgroundTasks`, CORS middleware if needed
- **M3U format**: Support both M3U and M3U8 formats; handle extended M3U attributes (#EXTINF, #EXTGRP)
- **Logging**: Use `logging.getLogger(__name__)` in every module; include key identifiers (channel URL, scan ID, validation status)
- **Data models**: All data passed between modules must use Pydantic BaseModels (never dataclass)
- **Rate limiting**: Default concurrency limit: 10 concurrent requests; configurable via CLI/config
- **Docker**: Multi-stage builds; include FFmpeg in final image; use non-root user; expose port 8000 for web interface
- **File size limit**: Each source file **must remain under 500 lines** (excluding comments/blanks)
  - If a module grows beyond this, refactor into smaller submodules
- **Module cohesion**: Each module should have a single clear responsibility; avoid deep import dependencies (limit to `utils/` and `models/`)

## Network Scanning Ethics and Safety

**Critical Guidelines**:

- **Local Network Only**: Only scan local network segments (192.168.x.x, 10.x.x.x, 172.16.x.x); never scan public internet ranges
- **Rate Limiting**: Default concurrency: 10 simultaneous requests; default timeout: 10 seconds per probe
- **Respect Robots.txt**: If scanning web servers, respect robots.txt directives
- **User Consent**: Clearly document in README that this tool is for personal network use only
- **Avoid DDoS Behavior**: Implement exponential backoff for failed requests; never retry more than 3 times
- **Legal Compliance**: Users must comply with local laws regarding network scanning and IPTV access

**Implementation Requirements**:

- Add `--max-concurrency` CLI option (default: 10, max: 50)
- Add `--timeout` CLI option (default: 10 seconds, max: 60)
- Log all network requests with timestamps and response codes
- Implement graceful shutdown on Ctrl+C (cancel pending requests)

## Task Complexity Threshold for iptv-sniffer

iptv-sniffer development involves both straightforward implementation tasks and complex technical decisions. Use the appropriate approach based on task complexity.

**Complex tasks requiring deep reasoning** (activate Sequential Thinking MCP):

- Network discovery strategies (UDP multicast vs HTTP probing vs SSDP)
- FFmpeg validation parameters (which codecs to check, timeout strategies, error interpretation)
- M3U format edge cases (non-standard attributes, character encoding issues)
- Concurrency control strategies (asyncio vs threading, rate limiting algorithms)
- Storage architecture decisions (JSON files vs SQLite vs in-memory with periodic persistence)
- Docker optimization strategies (multi-stage builds, FFmpeg bundling, image size reduction)

**Simple tasks** (direct execution without extended reasoning):

- Adding new CLI options or flags
- Fixing linter errors or type checking issues
- Writing unit tests for existing functions
- Adding logging statements or error messages
- Updating web interface HTML/CSS
- Adding new M3U attribute parsers

When in doubt, consider: Does this task involve evaluating tradeoffs between multiple technical approaches? If yes, use deep reasoning.

## Architecture Decision Records for iptv-sniffer

For significant architectural decisions in iptv-sniffer, create ADR documents in `docs/adr/` following the format defined in instructions.md.

**Create ADRs when deciding on**:

- Network discovery protocols and scanning strategies
  - Example: "0001-udp-multicast-discovery-strategy"
- FFmpeg validation approach and parameter selection
  - Example: "0002-ffmpeg-python-integration"
- M3U format support and compatibility layers
  - Example: "0003-extended-m3u-attribute-handling"
- Web framework selection (Flask vs FastAPI)
  - Example: "0004-fastapi-for-async-web-api"
- Storage backend architecture
  - Example: "0005-json-file-storage-for-simplicity"
- Docker image optimization strategies
  - Example: "0006-multi-stage-build-with-alpine-ffmpeg"

**ADR Storage in Memory**:

After creating an ADR, store the decision in the Knowledge Graph Memory:

```yaml
Entity: "[Decision Name]" (type: Technical Decision)
Observations:
  - "Decision rationale: [key reason]"
  - "Alternatives considered: [other options]"
  - "Performance impact: [metrics]"
Relations:
  - "documents" → "iptv-sniffer Architecture"
  - "influences" → "[Affected Module]"
```

## Knowledge Graph Memory for iptv-sniffer

This project uses the **`memory_iptv_sniffer`** MCP server configured in `config.toml`.

Query memory at task start to recall prior architectural decisions, performance benchmarks, and format compatibility constraints.

**Entity types for iptv-sniffer**:

- **Network Scanning Strategies**: Discovery protocols, timeout values, concurrency limits validated through testing
- **FFmpeg Integration Patterns**: Validation parameters, error handling approaches, timeout configurations
- **M3U Format Compatibility**: Supported attributes, character encoding decisions, parser edge cases
- **Performance Benchmarks**: Network scan speed, FFmpeg validation throughput, concurrent request limits
- **Docker Image Configurations**: Base image selection, FFmpeg installation method, final image size

**Example memory entry**:

```yaml
Entity: "FFmpeg Stream Validation Strategy"
  Type: Technical Decision
  Observations:
    - "Using ffmpeg-python library instead of subprocess for type safety"
    - "Default timeout: 10 seconds per stream probe"
    - "Validation checks: codec presence, bitrate non-zero, duration > 1 second"
    - "Error handling: catch ffmpeg.Error, parse stderr for diagnostics"
  Relations:
    - "implements" → "Stream Validator Module"
    - "documented in" → "ADR-0002-ffmpeg-python-integration"
```

Query memory at task start to recall prior architectural decisions, performance benchmarks, and format compatibility constraints.

## MCP Usage Scenarios for iptv-sniffer

**Sequential Thinking**: Use for complex technical design and tradeoff analysis

- Scenario: Designing network discovery protocol (UDP multicast vs HTTP probing)
- Scenario: Evaluating FFmpeg validation parameters and timeout strategies
- Scenario: Choosing between Flask and FastAPI for web framework
- Scenario: Planning Docker multi-stage build optimization

**Knowledge Graph Memory**: Store and query iptv-sniffer technical decisions

- Store: Network scanning parameters validated through testing
- Store: FFmpeg integration patterns and error handling strategies
- Query: "What was the rationale for using ffmpeg-python over subprocess?"
- Query: "What timeout values did we validate for stream probing?"

**Pydantic Docs**: Official Pydantic documentation for data validation models

- Scenario: Defining channel models (Channel, M3UPlaylist, StreamInfo)
- Scenario: Configuring field validation rules (URL format, non-negative durations)
- Scenario: Nested model structures (Playlist contains Channels)
- Scenario: Custom validators for M3U attribute parsing

**FFmpeg-Python Docs**: Official ffmpeg-python library documentation

- Scenario: Setting up FFmpeg input streams with timeout options
- Scenario: Capturing FFmpeg stderr output for diagnostics
- Scenario: Using FFmpeg filters for stream analysis
- Scenario: Handling FFmpeg errors and exit codes

**Flask Docs**: Official Flask framework documentation

- Scenario: Defining REST API routes with Flask blueprints
- Scenario: Serving static files via send_from_directory
- Scenario: Background task execution using threading
- Scenario: Request/response handling with Flask Request/Response objects

**FastAPI Docs**: Official FastAPI framework documentation

- Scenario: Defining async REST API routes with type hints
- Scenario: Request/response models using Pydantic
- Scenario: Background task execution via BackgroundTasks
- Scenario: CORS configuration using CORSMiddleware

**Aiohttp Docs**: Official aiohttp library documentation

- Scenario: Implementing concurrent HTTP requests with aiohttp.ClientSession
- Scenario: Managing connection pooling and timeout configuration
- Scenario: Handling network failures and retry strategies
- Scenario: Configuring client session parameters for IPTV stream scanning

**Context7**: General-purpose documentation for other dependencies

- Query: "M3U file format specification and extended attributes"
- Query: "Docker multi-stage build best practices for Python applications"
- Query: "HTTP probing techniques for IPTV stream discovery"

## Git Commit Conventions

iptv-sniffer follows conventional commits format for clear commit history and automated changelog generation.

**Commit message format**:

```text
type(scope): description

[optional body]
[optional footer]
```

**Common types and scopes for iptv-sniffer**:

- `feat(scanner)`: New network discovery feature or enhancement
- `feat(validator)`: New FFmpeg validation capability
- `feat(m3u)`: M3U parser or generator enhancement
- `feat(web)`: Web interface or API endpoint addition
- `feat(cli)`: New CLI command or option
- `fix(scanner)`: Bug fix in network scanning logic
- `fix(validator)`: Bug fix in stream validation
- `fix(m3u)`: M3U parsing or generation bug fix
- `refactor(scanner)`: Code restructuring without behavior change
- `test(validator)`: Adding or updating tests
- `docs(readme)`: Documentation updates
- `chore(docker)`: Docker configuration updates
- `chore(deps)`: Dependency updates

**Examples**:

```text
feat(scanner): add UDP multicast discovery for IPTV streams
fix(validator): handle FFmpeg timeout errors gracefully
test(m3u): add unit tests for extended M3U attribute parsing
refactor(web): extract API routes into separate modules
docs(scanner): document network scanning ethics and rate limits
chore(docker): optimize multi-stage build for smaller image size
```

## Development Workflow for iptv-sniffer

1. **Consult project documentation**: Read `AGENTS.md` and `README.md` to understand iptv-sniffer architecture, scanning strategies, and safety guidelines.

2. **Recall project context**: Check iptv-sniffer memory for prior network scanning strategies, FFmpeg validation parameters, and M3U format decisions relevant to the current task.

3. **For complex tasks** (see Task Complexity Threshold): Use deep reasoning to evaluate network discovery protocols, FFmpeg integration strategies, or concurrency control approaches before implementation.

4. **Verify API usage**: Use dedicated MCPs (pydantic_docs, ffmpeg_python_docs, flask_docs, fastapi_docs, aiohttp_docs) to confirm current API patterns for core dependencies; use Context7 for M3U format specifications and Docker best practices.

5. **For each new feature/enhancement**:

   - Write unit tests first using pytest framework (TDD approach)
   - Implement minimal code to pass tests
   - Enforce type safety: Pydantic models (never `dataclass`), avoid `Any` in public APIs
   - Use `ffmpeg-python` library (never subprocess command strings)
   - Keep each source file under 500 lines (excluding comments/blanks)
   - Run `pytest` and `mypy` to verify no errors
   - If file approaches 450 lines, refactor into submodules

6. **Test network scanning features**:

   - Test rate limiting with concurrent requests
   - Test timeout handling with slow/unresponsive endpoints
   - Test graceful shutdown on Ctrl+C
   - Verify no network abuse (check request frequency)

7. **Test FFmpeg integration**:

   - Test with valid IPTV streams (HTTP, UDP, RTSP)
   - Test with invalid/unreachable streams
   - Test timeout enforcement (should not hang indefinitely)
   - Verify error messages are clear and actionable

8. **Test Docker deployment**:

   - Build Docker image and verify FFmpeg is included
   - Run container and verify web interface is accessible
   - Test volume mounts for persistent storage
   - Verify health check endpoint responds correctly

9. **Document decisions**: For significant architectural choices (scanning strategies, FFmpeg parameters, storage architecture), create ADR in `docs/adr/` and store in memory.

10. **Commit changes**: Use conventional commits format (see Git Commit Conventions) and commit all modified files.

## Code Quality Requirements

Before merging changes to iptv-sniffer, ensure:

**Testing & Type Safety**:

- All tests pass: `pytest`
- Type checking passes: `mypy --strict`
- Linter reports no infractions: `ruff check`
- Public APIs have type hints, no `Any` in signatures

**Code Quality**:

- Each source file remains under 500 lines (excluding comments/blanks)
- Logging messages include key identifiers (channel URL, scan ID, validation status, timestamps)
- Network requests include proper timeouts and error handling
- FFmpeg operations use `ffmpeg-python` library (no subprocess strings)
- Rate limiting is enforced for all network operations

**Network Scanning Safety**:

- Concurrency limits are configurable and enforced
- Timeout values are reasonable (10s default, 60s max)
- Graceful shutdown implemented (cancel pending requests)
- Logging includes network request metadata (URL, duration, status)

**Docker Quality**:

- Dockerfile uses multi-stage builds
- Final image size < 500MB (with FFmpeg)
- Runs as non-root user
- Health check endpoint defined
- Environment variables documented

**Documentation**:

- New features documented in README with example usage
- Network scanning ethics documented clearly
- CLI help messages are clear and complete
- API endpoints documented (OpenAPI/Swagger if using FastAPI)
- Significant decisions captured in ADR (see Architecture Decision Records)

**M3U Format Compliance**:

- M3U parser handles extended attributes (#EXTINF, #EXTGRP, etc.)
- Character encoding handled correctly (UTF-8 default)
- Generated M3U files validated against spec
- Error messages clear for invalid M3U files

**FFmpeg Integration**:

- All FFmpeg calls use `ffmpeg-python` library
- Timeouts enforced on all stream probes
- FFmpeg stderr captured and logged for diagnostics
- Error handling covers common FFmpeg failure modes

## Web Interface Guidelines

**Frontend Requirements**:

- Single-page interface for simplicity (HTML + vanilla JS or lightweight framework)
- Responsive design (mobile-friendly)
- Real-time scan progress updates (via WebSocket or polling)
- Channel list with filtering and sorting
- M3U import/export via file upload/download

**Backend API Design**:

- RESTful endpoints: `GET /api/channels`, `POST /api/scan`, `GET /api/export`
- JSON request/response format with Pydantic validation
- Background task support for long-running scans
- Health check endpoint: `GET /health` (returns 200 OK)
- Static file serving: serve `index.html` at root `/`

**CORS Configuration** (if needed):

- Allow origins: configurable via environment variable
- Allow methods: GET, POST, DELETE
- Allow headers: Content-Type

## Docker Deployment Best Practices

**Dockerfile Structure**:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Final image with FFmpeg
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
COPY iptv_sniffer /app/iptv_sniffer
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
USER nobody
CMD ["python", "-m", "iptv_sniffer.web.app"]
```

**docker-compose.yml**:

```yaml
version: "3.8"
services:
  iptv-sniffer:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - MAX_CONCURRENCY=10
      - TIMEOUT=10
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

**Environment Variables**:

- `MAX_CONCURRENCY`: Maximum concurrent network requests (default: 10)
- `TIMEOUT`: Network request timeout in seconds (default: 10)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DATA_DIR`: Directory for persistent storage (default: /app/data)

---

**Remember**: This is a network scanning tool with ethical implications. Always prioritize user safety, network respect, and legal compliance. Implement robust rate limiting and clear documentation about proper usage.

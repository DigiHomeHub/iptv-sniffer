# IPTV Sniffer

A lightweight tool to discover and validate IPTV channels on local networks

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

## Overview

`iptv-sniffer` is a production-ready network tool designed to discover, validate, and manage IPTV channels across local networks. It combines powerful backend scanning capabilities with an intuitive web interface, supporting multiple scanning strategies, M3U playlist management, and FFmpeg-based stream validation.

**Key capabilities:**

- 🔍 **Multi-strategy scanning**: HTTP template-based, RTP/UDP multicast, and M3U batch validation
- 📺 **Multi-protocol support**: HTTP(S), RTP, RTSP, UDP, MMS stream validation
- 📄 **M3U management**: Import/export playlists with extended attribute support (tvg-id, tvg-logo, group-title)
- 🖼️ **Visual preview**: Automatic screenshot capture for channel identification
- 🌐 **Modern web UI**: Vue 3 + Vite interface with responsive design
- 🐳 **Docker-ready**: Multi-stage builds with <500MB image size
- ⚡ **Performance optimizations**: Smart port scanning reduces multicast scan time by 80%

---

## Features

### Network Scanning

- **Template-based HTTP scanning**: Discover channels using URL patterns (e.g., `http://192.168.2.{ip}:8000/rtp/channel`)
- **Multicast RTP/UDP scanning**: Detect IPTV services on multicast addresses (239.x.x.x)
- **Smart port scanner**: Two-phase optimization reduces scan duration from 21 hours to 3.6 hours for typical multicast scenarios
- **Scan presets**: Curated templates for common IPTV providers (Beijing Unicom, Shanghai Telecom, etc.)

### Stream Validation

- **FFmpeg-based validation**: Reliable stream probing with codec detection and resolution extraction
- **Protocol-specific configurations**: Optimized settings for RTP (20s timeout, multicast buffer tuning), RTSP (TCP transport), and HTTP streams
- **Hardware acceleration**: Optional VAAPI (Intel Quick Sync) and CUDA (NVIDIA) support for faster processing
- **Screenshot capture**: Automatic thumbnail generation with lazy loading and error fallback

### M3U Playlist Management

- **Import**: Parse M3U/M3U8 files with character encoding detection (UTF-8, GB2312, GBK, Big5)
- **Export**: Generate standards-compliant playlists with grouping and sorting options
- **Extended attributes**: Full support for tvg-id, tvg-name, tvg-logo, and group-title metadata
- **Batch validation**: Auto-prompt for channel validation after import

### Modern Web UI

- **Vue 3 + TypeScript**: Modern reactive UI with type safety
- **Four main pages**:
  - **Stream Test**: Quick URL validation with instant results
  - **TV Channels**: Browse, filter, sort, and manage discovered channels
  - **TV Groups**: Organize channels by category
  - **Advanced Settings**: Configure scan parameters and presets
- **Real-time updates**: Scan progress tracking with HTTP polling
- **Responsive design**: Mobile-friendly layout

### Data Management

- **JSON-based storage**: Human-readable channel database with atomic writes
- **URL deduplication**: Prevents duplicate entries while preserving manual edits
- **Repository pattern**: Clean abstraction enables future SQLite migration

---

## Technology Stack

### Backend

| Component             | Technology                   | Purpose                          |
| --------------------- | ---------------------------- | -------------------------------- |
| **Web Framework**     | FastAPI 0.120+               | Async REST API with OpenAPI docs |
| **Stream Validation** | FFmpeg-python 0.2+           | Type-safe FFmpeg integration     |
| **Data Validation**   | Pydantic 2.12+               | Type-safe models and settings    |
| **Concurrency**       | asyncio + ThreadPoolExecutor | Hybrid async-thread model        |
| **CLI Framework**     | Typer 0.12+                  | Command-line interface           |
| **Type Checking**     | Pyrefly 0.39+                | Strict type enforcement          |

### Frontend

| Component       | Technology          | Purpose                          |
| --------------- | ------------------- | -------------------------------- |
| **Framework**   | Vue 3.5+            | Reactive UI with Composition API |
| **Build Tool**  | Vite 6+             | Fast HMR and optimized builds    |
| **Language**    | TypeScript 5+       | Type safety                      |
| **Styling**     | Tailwind CSS 3+     | Utility-first CSS                |
| **HTTP Client** | Axios 1.7+          | REST API communication           |
| **Testing**     | Vitest + Playwright | Unit and E2E testing             |

### Deployment

| Component            | Technology     | Purpose                    |
| -------------------- | -------------- | -------------------------- |
| **Containerization** | Docker         | Multi-stage builds         |
| **Orchestration**    | Docker Compose | Development and production |
| **ASGI Server**      | Uvicorn 0.38+  | Production HTTP server     |

---

## Prerequisites

### For Docker Deployment (Recommended)

- Docker 20.10+
- Docker Compose 1.29+ (optional, for orchestration)

### For Local Development

- **Python**: 3.12 or higher
- **FFmpeg**: 4.4 or higher (with `libavcodec-extra` for additional codec support)
- **Node.js**: 18+ (for frontend development)
- **uv** (recommended) or **pip**: Python package manager

#### Installing FFmpeg

**macOS** (Homebrew):

```bash
brew install ffmpeg
```

**Ubuntu/Debian**:

```bash
sudo apt update && sudo apt install -y ffmpeg libavcodec-extra
```

**Windows** (Chocolatey):

```bash
choco install ffmpeg
```

---

## Quick Start (Docker)

The fastest way to run iptv-sniffer is using Docker:

### 1. Build the Docker image

```bash
./scripts/docker-build.sh
```

Or manually:

```bash
docker build -t iptv-sniffer:latest .
```

### 2. Run the container

```bash
./scripts/docker-run.sh
```

Or manually:

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --name iptv-sniffer \
  iptv-sniffer:latest
```

### 3. Access the web interface

Open your browser and navigate to:

```text
http://localhost:8000
```

The web interface provides:

- **Stream Test** page for quick URL validation
- **TV Channels** page for browsing and managing channels
- **M3U Import/Export** functionality
- **Scan Configuration** with preset templates

---

## Installation (Local Development)

### Backend Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/DigiHomeHub/iptv-sniffer.git
   cd iptv-sniffer
   ```

2. **Install Python dependencies** (using `uv`):

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   uv pip install --group dev
   ```

3. **Verify FFmpeg installation**:

   ```bash
   python -c "from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed; check_ffmpeg_installed()"
   ```

### Frontend Setup

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:

   ```bash
   npm install
   ```

3. **Start development server**:

   ```bash
   npm run dev
   ```

The frontend dev server runs on `http://localhost:5173` with HMR enabled.

### Running Both Servers

**Terminal 1 (Backend)**:

```bash
uvicorn iptv_sniffer.web.app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend)**:

```bash
cd frontend && npm run dev
```

The frontend Vite server proxies `/api` requests to the backend on port 8000.

---

## Usage

### Web Interface

1. **Stream Test**: Validate a single IPTV URL

   - Enter stream URL (e.g., `http://192.168.2.100:8000/channel1`)
   - Click "Test Stream"
   - View validation results (codec, resolution, screenshot)

2. **Network Scan**:

   - Choose a scan strategy:
     - **Template**: Provide URL pattern with `{ip}` placeholder
     - **Multicast**: Configure IP range and port list
     - **Preset**: Select from curated IPTV provider templates
   - Configure scan options (concurrency, timeout)
   - Monitor real-time progress
   - Browse discovered channels in **TV Channels** page

3. **M3U Import**:

   - Navigate to **TV Channels** → Import M3U
   - Drag-and-drop or select M3U file
   - Character encoding auto-detected (UTF-8, GB2312, GBK)
   - Optionally validate imported channels

4. **M3U Export**:
   - Navigate to **TV Channels** → Export M3U
   - Select export format (M3U or M3U8)
   - Choose filtering and sorting options
   - Download generated playlist

### CLI Commands

The `iptv-sniffer` CLI provides command-line access to core functionality:

#### Display Version

```bash
iptv-sniffer --version
```

#### Scan Networks (Template Strategy)

```bash
iptv-sniffer scan --template "http://192.168.2.{ip}:8000/rtp/channel" \
  --start-ip 192.168.2.100 \
  --end-ip 192.168.2.200 \
  --max-concurrency 10 \
  --timeout 10
```

#### Scan Multicast (Preset)

```bash
iptv-sniffer scan --preset beijing-unicom
```

#### Validate Channels

```bash
iptv-sniffer validate --all
```

#### Export M3U Playlist

```bash
iptv-sniffer export --output channels.m3u --format m3u8 --group "Sports"
```

#### List Discovered Channels

```bash
iptv-sniffer list --group "Sports" --status online
```

**Note**: CLI commands are placeholder implementations. Full CLI functionality is planned for v1.1.

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Scan Settings
MAX_CONCURRENCY=10          # Maximum concurrent network requests (1-50)
SCAN_TIMEOUT=10             # Network request timeout in seconds (1-60)
RATE_LIMIT=50               # Maximum requests per second

# FFmpeg Settings
FFMPEG_HW_ACCEL=            # Hardware acceleration: "vaapi" (Intel) or "cuda" (NVIDIA)
FFMPEG_SCREENSHOT_DIR=./data/screenshots  # Screenshot storage path

# Storage Settings
DATA_DIR=./data             # Channel database directory
CHANNELS_FILE=channels.json # Channel database filename

# Web Server
UVICORN_HOST=0.0.0.0        # Bind address
UVICORN_PORT=8000           # Bind port
UVICORN_LOG_LEVEL=info      # Logging level: debug, info, warning, error
```

### Configuration File (YAML)

Alternatively, create `config.yaml`:

```yaml
scan:
  max_concurrency: 10
  timeout: 10
  rate_limit: 50

ffmpeg:
  hw_accel: null # "vaapi" or "cuda"
  screenshot_dir: ./data/screenshots

storage:
  data_dir: ./data
  channels_file: channels.json
```

### Scan Presets

Edit `config/multicast_presets.json` to add custom IPTV provider templates:

```json
{
  "custom-isp": {
    "name": "Custom ISP",
    "protocol": "rtp",
    "ip_ranges": ["239.1.1.1-239.1.1.255"],
    "ports": [8000, 8001, 8002],
    "estimated_duration": "2 hours",
    "reference_url": "https://example.com/iptv-guide"
  }
}
```

---

## Development

### Project Structure

```text
iptv-sniffer/
├── frontend/              # Vue 3 + Vite frontend
│   ├── src/
│   │   ├── api/          # REST API client (Axios)
│   │   ├── components/   # Reusable Vue components
│   │   ├── views/        # Page-level components
│   │   ├── router/       # Vue Router configuration
│   │   └── types/        # TypeScript type definitions
│   └── tests/            # Vitest unit tests + Playwright E2E
├── iptv_sniffer/         # Python backend
│   ├── cli/              # Typer CLI application
│   ├── scanner/          # Network scanning strategies
│   ├── m3u/              # M3U parser and generator
│   ├── channel/          # Channel data models
│   ├── storage/          # JSON repository
│   ├── utils/            # FFmpeg helpers and config
│   └── web/              # FastAPI application
│       ├── api/          # REST API endpoints
│       └── static/       # Built Vue frontend (Vite output)
├── tests/                # Python tests (unittest)
├── config/               # Scan presets
├── docs/                 # Architecture documentation
├── scripts/              # Docker build and run scripts
└── Dockerfile            # Multi-stage Docker build
```

### Running Tests

#### Backend Tests (Python)

```bash
# Run all tests with coverage
uv run pytest --cov=iptv_sniffer --cov-report=html tests/unit/

# Run specific test module
uv run python -m unittest tests.unit.scanner.test_validator -v

# Run with testmon (smart test selection)
uv run pytest --testmon tests/unit/
```

#### Frontend Tests (Vue)

```bash
# Unit tests (Vitest)
cd frontend && npm run test:unit

# Unit tests with coverage
npm run test:unit -- --coverage

# E2E tests (Playwright)
npm run test:e2e

# Type checking
npm run type-check
```

#### Integration Tests

```bash
# Docker build test
./tests/integration/test_docker_build.sh

# Docker health check
uv run pytest tests/integration/test_docker_health.py
```

### Code Quality Checks

```bash
# Type checking (Pyrefly)
uv run pyrefly check

# Linting (Ruff)
uv run ruff check

# Formatting (Ruff)
uv run ruff format

# Pre-commit hooks (all checks)
pre-commit run --all-files
```

### Building for Production

#### Frontend Build

```bash
cd frontend && npm run build
```

Output: `iptv_sniffer/web/static/`

#### Docker Build

```bash
docker build -t iptv-sniffer:latest .
```

**Image size**: <500MB (including FFmpeg)

---

## Architecture

### High-Level Overview

```mermaid
graph TD
    A[Vue 3 + Vite<br/>Web Interface<br/>(TypeScript + Tailwind CSS)] -->|HTTP/REST API| B[FastAPI<br/>Web Server<br/>(Python 3.12+)]
    B --> C[Scanner Strategies<br/>- Template<br/>- Multicast<br/>- M3U Batch]
    B --> D[M3U Parser &amp; Generator<br/>- UTF-8/GB*<br/>- Extended Attributes]
    C --> E[Stream Validator<br/>(FFmpeg)]
    E --> F[JSON Storage Repository<br/>- Atomic write<br/>- Deduplication]
    D --> F
```

### Key Design Decisions

1. **Strategy Pattern for Scanning**: Pluggable scan strategies (Template, Multicast, M3U Batch) enable Open/Closed Principle.

2. **Hybrid Async-Thread Concurrency**: asyncio for network I/O + ThreadPoolExecutor for blocking FFmpeg calls. Balances performance with rate limiting ethics.

3. **Repository Pattern for Storage**: Abstraction layer enables future migration from JSON to SQLite without changing business logic.

4. **FFmpeg-Python Library**: Type-safe FFmpeg integration prevents command injection vulnerabilities compared to subprocess string concatenation.

5. **Vue 3 + Vite Frontend**: Saves 132 development hours over vanilla JS across v1.0-v2.0 lifecycle.

6. **Docker Multi-Stage Build**: Separates frontend build (Node), backend dependencies (uv), and final runtime (FFmpeg) for <500MB images.

### Performance Optimizations

- **Smart Port Scanner**: Two-phase multicast scanning reduces target count by 83% (7,650 → 1,300 URLs)
- **Rate Limiting**: Configurable concurrency (default: 10) prevents network abuse
- **Lazy Loading**: Frontend defers screenshot loading until viewport visibility
- **Vite Chunking**: Code splitting reduces initial bundle size to <200KB

---

## Testing

### Test Coverage

| Module             | Backend Coverage | Frontend Coverage |
| ------------------ | ---------------- | ----------------- |
| Scanner            | 100%             | -                 |
| M3U Parser         | 100%             | -                 |
| Stream Validator   | 100%             | -                 |
| Channel Repository | 100%             | -                 |
| Web API            | 95%              | -                 |
| Vue Components     | -                | 85%               |
| **Overall**        | **>95%**         | **>80%**          |

### Testing Strategy

- **Backend**: TDD with unittest framework, `IsolatedAsyncioTestCase` for async code
- **Frontend**: Vitest for component unit tests, Playwright for E2E workflows
- **Integration**: Docker build validation, health check endpoints, API contract tests

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch from `main`
2. **Follow GitHub Flow**: All changes via Pull Requests
3. **Write tests first** (TDD approach): Red → Green → Refactor
4. **Ensure quality gates pass**:
   - Backend: `uv run pytest`, `uv run pyrefly check`, `uv run ruff check`
   - Frontend: `npm run test:unit`, `npm run type-check`, `npm run lint`
5. **Use conventional commits**: `feat(scanner): add UDP multicast discovery`
6. **Keep files under 500 lines** (excluding comments/blanks)
7. **Update documentation** for new features

### Development Workflow

See [AGENTS.md](AGENTS.md) for comprehensive development guidelines, including:

- Project architecture and module responsibilities
- TDD workflow with unittest and Vitest
- Network scanning ethics and rate limiting
- FFmpeg integration best practices
- Docker deployment patterns

### Task Prompts

Detailed TDD task prompts are available in [docs/prompts/](docs/prompts/README.md) covering:

- Phase 1: Core Infrastructure (Channel models, Config, Storage, CLI)
- Phase 2: FFmpeg Integration (Validation, Screenshots)
- Phase 3: Network Scanning (Strategies, Rate limiter, Orchestrator)
- Phase 4: M3U Support (Parser, Encoding, Generator)
- Phase 5: Multicast Support (Multicast strategy, Smart scanner, Presets)
- Phase 6: Web API (FastAPI setup, Endpoints)
- Phase 7: Frontend (Vue 3 + Vite interface)
- Phase 8: Docker Deployment (Multi-stage builds)

---

## Roadmap

### v1.1 (Planned)

- [ ] WebSocket support for real-time scan progress (replace HTTP polling)
- [ ] M3U Batch Strategy integration with ScanOrchestrator
- [ ] CLI command implementations (currently placeholders)
- [ ] SQLite storage backend option
- [ ] Fuzzy channel name deduplication
- [ ] EPG (Electronic Program Guide) integration

### v1.2 (Future)

- [ ] SSDP/UPnP automatic discovery
- [ ] Custom protocol adapters (plugin system)
- [ ] Multi-language support (i18n)
- [ ] Channel playlist management (favorites, custom groups)
- [ ] Scheduled re-validation (cron-like)

---

## Network Scanning Ethics

**⚠️ Important Guidelines**:

- **Local Networks Only**: Only scan private IP ranges (10.x.x.x, 172.16-31.x.x, 192.168.x.x)
- **Rate Limiting**: Default concurrency limited to 10 concurrent requests
- **User Consent**: This tool is for personal network use only
- **Legal Compliance**: Users must comply with local laws regarding network scanning and IPTV access
- **No DDoS Behavior**: Exponential backoff for failed requests, maximum 3 retries

**Security Features**:

- RFC1918 private network validation enforced
- Maximum 1024 IPs per scan to prevent abuse
- Configurable timeout (default: 10s, max: 60s)
- Graceful shutdown on Ctrl+C (cancels pending requests)

---

## Troubleshooting

### FFmpeg Not Found

**Error**: `FFmpegNotFoundError: FFmpeg is not installed or not in PATH`

**Solution**:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg libavcodec-extra

# Verify installation
ffmpeg -version
```

### Docker Build Fails

**Error**: `COPY failed: no source files were specified`

**Solution**: Ensure frontend is built before Docker build:

```bash
cd frontend && npm run build && cd ..
docker build -t iptv-sniffer:latest .
```

### Port 8000 Already in Use

**Error**: `uvicorn.error: [Errno 48] Address already in use`

**Solution**: Change port in `.env` or Docker command:

```bash
docker run -p 8080:8000 iptv-sniffer:latest
# Access at http://localhost:8080
```

### Multicast Scan Too Slow

**Problem**: Scanning 239.3.1.1-255 with 30 ports takes 21 hours

**Solution**: Enable smart port scanner (enabled by default):

```bash
iptv-sniffer scan --preset beijing-unicom --smart-scan
# Reduces duration to ~3.6 hours (80% faster)
```

---

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Inspired by**: [thsrite/iptv-sniff](https://github.com/thsrite/iptv-sniff)
- **FFmpeg**: The backbone of stream validation and screenshot capture
- **FastAPI**: Modern async web framework with excellent OpenAPI integration
- **Vue 3**: Reactive frontend framework with outstanding developer experience
- **Vite**: Blazingly fast frontend build tool

---

## Contact

For questions, feature requests, or bug reports, please open an issue on [GitHub Issues](https://github.com/DigiHomeHub/iptv-sniffer/issues).

**Project Links**:

- Documentation: [docs/Design.md](docs/Design.md)
- Architecture Decisions: [docs/adr/](docs/adr/)
- Development Guide: [AGENTS.md](AGENTS.md)
- Task Prompts: [docs/prompts/README.md](docs/prompts/README.md)

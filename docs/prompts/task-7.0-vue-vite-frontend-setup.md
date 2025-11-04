# Task 7.0: Vue 3 + Vite Frontend Setup

## Overview

Initialize Vue 3 + Vite frontend project with TypeScript, Tailwind CSS, and Headless UI. Configure Vite proxy for FastAPI backend integration and set up production build pipeline.

**Priority**: P0 - Critical foundation for all frontend development

**Estimated Duration**: 4-6 hours

## Design Context

This task implements the Vue 3 + Vite frontend architecture decision for iptv-sniffer, replacing the original Vanilla JS approach. The decision was made to:

- **Leverage Vue's reactive system** for complex UI state management (scan progress, channel lists, filters)
- **Use TypeScript** for type safety aligned with backend Pydantic models
- **Adopt Vite** for fast HMR development experience and optimized production builds
- **Maintain Tailwind CSS** for utility-first styling with minimal framework overhead

See development-plan.md Phase 7 for complete architecture rationale.

## Prerequisites

**Completed Tasks**:

- Task 6.1: FastAPI Setup (backend API foundation)
- Task 6.2: Scan Endpoints (scan API ready for integration)

**System Requirements**:

- Node.js >= 18.0.0
- npm >= 9.0.0
- Python 3.11+ with FastAPI running

## TDD Guide

### Red: Write Failing Tests

```python
# tests/unit/web/test_frontend_build.py

import subprocess
from pathlib import Path
import pytest


class TestFrontendBuild:
    """Test frontend build and configuration"""

    def test_frontend_directory_exists(self):
        """Frontend directory should exist"""
        frontend_dir = Path("frontend")
        assert frontend_dir.exists()
        assert (frontend_dir / "package.json").exists()

    def test_vite_config_exists(self):
        """Vite configuration should be present"""
        vite_config = Path("frontend/vite.config.ts")
        assert vite_config.exists()

    def test_vite_config_proxy_configured(self):
        """Vite should proxy API requests to FastAPI backend"""
        vite_config = Path("frontend/vite.config.ts")
        content = vite_config.read_text()
        assert "proxy" in content
        assert "/api" in content
        assert "localhost:8000" in content

    def test_frontend_build_succeeds(self):
        """Frontend build should complete without errors"""
        frontend_dir = Path("frontend")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        assert (Path("iptv_sniffer/web/static/index.html")).exists()

    def test_tailwind_css_configured(self):
        """Tailwind CSS should be properly configured"""
        tailwind_config = Path("frontend/tailwind.config.js")
        assert tailwind_config.exists()
        content = tailwind_config.read_text()
        assert "content" in content
        assert "./src/**/*.vue" in content
```

Run tests (should fail):

```bash
uv run python -m unittest discover -s tests/unit/web -p 'test_frontend_build.py' -v
```

### Green: Implement Minimal Solution

#### Step 1: Initialize Vite + Vue Project

```bash
cd ~/workspace/iptv-sniffer

# Create Vue 3 + TypeScript project with Vite
npm create vite@latest frontend -- --template vue-ts

cd frontend

# Install dependencies
npm install

# Install Tailwind CSS + PostCSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install Headless UI for accessible components
npm install @headlessui/vue

# Install Axios for HTTP client
npm install axios

# Install Vue Router (optional for Task 7.1)
npm install vue-router@4
```

#### Step 2: Configure Vite with Proxy

```typescript
// frontend/vite.config.ts

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path, // Keep /api prefix
      },
    },
  },
  build: {
    outDir: "../iptv_sniffer/web/static",
    emptyOutDir: true,
    assetsDir: "assets",
  },
});
```

#### Step 3: Configure Tailwind CSS

```javascript
// frontend/tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
      },
    },
  },
  plugins: [],
};
```

```css
/* frontend/src/style.css */

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  /* Button Variants */
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2;
  }

  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400;
  }

  .btn-danger {
    @apply bg-red-600 text-white hover:bg-red-700 focus:ring-red-500;
  }

  /* Card Component */
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }

  /* Form Inputs */
  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md
           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
  }

  .input-label {
    @apply block text-sm font-medium text-gray-700 mb-1;
  }

  /* Progress Bar */
  .progress-bar {
    @apply h-2 bg-blue-600 rounded-full transition-all duration-300;
  }
}
```

#### Step 4: Create API Client Layer

```typescript
// frontend/src/api/client.ts

import axios, { AxiosInstance, AxiosResponse, AxiosError } from "axios";

const apiClient: AxiosInstance = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    const message =
      (error.response?.data as any)?.detail ||
      error.message ||
      "Request failed";
    console.error("API Error:", message, error.response);
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
```

```typescript
// frontend/src/api/scan.ts

import apiClient from "./client";

export interface ScanStartRequest {
  mode: "template" | "multicast" | "m3u_batch";
  base_url?: string;
  start_ip?: string;
  end_ip?: string;
  protocol?: string;
  ip_ranges?: string[];
  ports?: number[];
  timeout?: number;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: "pending" | "running" | "completed" | "cancelled" | "failed";
  progress: number;
  total: number;
  valid: number;
  invalid: number;
  started_at: string;
  completed_at?: string;
}

export const scanAPI = {
  /**
   * Start a new scan with specified configuration
   */
  start: async (data: ScanStartRequest) => {
    const response = await apiClient.post<{
      scan_id: string;
      status: string;
      estimated_targets: number;
    }>("/scan/start", data);
    return response.data;
  },

  /**
   * Get scan status by scan ID
   */
  getStatus: async (scanId: string) => {
    const response = await apiClient.get<ScanStatusResponse>(`/scan/${scanId}`);
    return response.data;
  },

  /**
   * Cancel running scan
   */
  cancel: async (scanId: string) => {
    const response = await apiClient.delete<{ cancelled: boolean }>(
      `/scan/${scanId}`
    );
    return response.data;
  },
};
```

#### Step 5: Update FastAPI to Serve Vue Build

```python
# iptv_sniffer/web/app.py (modify existing)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="iptv-sniffer",
    description="Discover and validate IPTV channels on local networks",
    version=__version__
)

# Mount static files (Vue build output)
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    # Production mode: serve Vue build
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    logger.info(f"Serving Vue SPA from {static_dir}")
else:
    logger.warning(f"Static directory not found at {static_dir}. Run 'npm run build' in frontend/")

# API routes registration (existing)
from iptv_sniffer.web.api import scan
app.include_router(scan.router)

# Catch-all route to serve Vue SPA (must be last)
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(request: Request, full_path: str):
    """
    Serve Vue SPA for all non-API routes (Vue Router history mode).
    API routes are handled by FastAPI routers above.
    """
    # Check if request is for an API route
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}, 404

    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # Development mode message
    return {
        "message": "Frontend not built. Run 'npm run dev' in frontend/ directory for development.",
        "build_command": "npm run build (in frontend/) to create production build"
    }
```

#### Step 6: Update package.json Scripts

```json
// frontend/package.json (add scripts)

{
  "name": "iptv-sniffer-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "type-check": "vue-tsc --noEmit"
  },
  "dependencies": {
    "@headlessui/vue": "^1.7.16",
    "axios": "^1.6.2",
    "vue": "^3.3.8",
    "vue-router": "^4.2.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.0",
    "@vue/tsconfig": "^0.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.2",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.22"
  }
}
```

### Refactor: Improve Code Quality

**Type Safety Improvements**:

```typescript
// frontend/src/types/api.ts

// Centralize all API types
export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
}

// Re-export scan types
export type { ScanStartRequest, ScanStatusResponse } from "@/api/scan";
```

**Environment Variables**:

```typescript
// frontend/src/config.ts

export const config = {
  apiBaseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  apiTimeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  pollInterval: 1000, // ms
} as const;
```

```bash
# frontend/.env.development

VITE_API_BASE_URL=/api
VITE_API_TIMEOUT=30000
```

## Verification

### Manual Testing

1. **Development Mode**:

   ```bash
   # Terminal 1: Start FastAPI backend
   cd ~/workspace/iptv-sniffer
   uv run uvicorn iptv_sniffer.web.app:app --reload --port 8000

   # Terminal 2: Start Vite dev server
   cd frontend
   npm run dev
   ```

   Visit <http://localhost:5173> - should see Vue app with HMR working

2. **Production Build**:

   ```bash
   cd frontend
   npm run build

   # Verify build output
   ls -la ../iptv_sniffer/web/static/
   # Should see: index.html, assets/

   # Start FastAPI to serve build
   cd ..
   uv run uvicorn iptv_sniffer.web.app:app --port 8000
   ```

   Visit <http://localhost:8000> - should see production Vue build

3. **API Proxy Test**:

   ```bash
   # In browser console (dev mode at localhost:5173):
   fetch('/api/health').then(r => r.json()).then(console.log)
   # Should return: {status: "ok", version: "0.1.0", checks: {...}}
   ```

### Automated Testing

```bash
# Run frontend build tests
uv run python -m unittest discover -s tests/unit/web -p 'test_frontend_build.py' -v

# Run type checking
cd frontend
npm run type-check

# Verify Vite build
npm run build
```

### Definition of Done Checklist

- [ ] Vite project initialized with Vue 3 + TypeScript template
- [ ] Tailwind CSS configured with custom components
- [ ] Vite proxy correctly forwards /api requests to FastAPI (localhost:8000)
- [ ] Frontend build outputs to iptv_sniffer/web/static/
- [ ] FastAPI serves Vue SPA for non-API routes (catch-all)
- [ ] API client with Axios and error handling implemented
- [ ] Development server runs on <http://localhost:5173> with HMR
- [ ] Production build verified (npm run build succeeds)
- [ ] All tests pass
- [ ] Type checking passes (vue-tsc)
- [ ] No lint errors

## Commit Template

```text
feat(web): initialize Vue 3 + Vite frontend with TypeScript

- Add Vite + Vue 3 project with TypeScript template
- Configure Tailwind CSS with custom component styles
- Set up Vite proxy to FastAPI backend (localhost:8000)
- Implement typed Axios API client with error handling
- Configure production build to output to iptv_sniffer/web/static/
- Update FastAPI to serve Vue SPA with catch-all route

Build outputs to static/ directory for Docker integration.
Development mode uses Vite dev server with HMR on port 5173.

Closes #<issue-number>
```

## Common Pitfalls

1. **Vite Proxy Not Working**:

   - Ensure FastAPI is running on port 8000
   - Check Vite config target URL matches backend
   - Verify `changeOrigin: true` in proxy config

2. **Build Output Path Issues**:

   - Verify `build.outDir` is correct relative path
   - Check FastAPI static file mounting path matches build output
   - Ensure `emptyOutDir: true` to avoid stale files

3. **TypeScript Path Alias Not Resolving**:

   - Verify `@` alias in both vite.config.ts and tsconfig.json
   - Restart Vite dev server after tsconfig changes

4. **Tailwind Styles Not Applied**:

   - Check `content` paths in tailwind.config.js include all Vue files
   - Verify `style.css` imports Tailwind directives
   - Ensure `style.css` is imported in main.ts

5. **API Requests Failing in Production**:
   - Verify FastAPI catch-all route is registered last
   - Check static files are served before catch-all
   - Ensure `baseURL` in Axios uses relative path `/api`

## Next Steps

- **Task 7.1**: Implement Vue Router with tab navigation
- **Task 7.2**: Build Stream Test page Vue component
- **Task 7.3**: Implement Channel Management API integration

## References

- [Vue 3 Documentation](https://vuejs.org/guide/)
- [Vite Configuration](https://vitejs.dev/config/)
- [Tailwind CSS v3](https://tailwindcss.com/docs)
- [Headless UI Vue](https://headlessui.com/vue/)
- [Axios Documentation](https://axios-http.com/docs/intro)

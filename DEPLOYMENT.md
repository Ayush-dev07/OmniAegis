# OmniAegis Deployment (No GCP)

This project is ready to deploy without GCP billing by splitting services:

- Frontend (`frontend/OmniAegis-Frontend-main`) -> Vercel
- Backend API (`decision_layer`) -> Render (Docker)
- Analysis Engine (`analysis_engine`) -> Render (Docker)

## 1) Deploy backend services on Render

Render blueprint file is already included at `render.yaml`.

1. Push this repo to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select this repo and confirm `render.yaml`.
4. Add all required secret env vars in Render dashboard:
   - `REDIS_URL`
   - `DATABASE_URL`
   - `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
   - `QDRANT_URL`, `QDRANT_API_KEY`
   - `GRAFANA_PROMETHEUS_URL`, `GRAFANA_API_KEY`
   - `PINATA_API_KEY`
   - `WEB3_PROVIDER_URL`

## 2) Deploy frontend on Vercel

1. Import this GitHub repo in Vercel.
2. Set **Root Directory** to `frontend/OmniAegis-Frontend-main`.
3. Build Command: `npm run build` (default is fine).
4. Start Command: `npm start` (for non-serverless runtime) or default Next.js runtime.
5. Add frontend env vars (example):
   - `NEXT_PUBLIC_API_URL=<decision-layer-url>`
   - any Firebase/public keys needed by the UI.

## 3) Local verification with Docker Compose

From repo root:

```bash
docker compose up --build
```

Expected local endpoints:

- Frontend: `http://localhost:3000`
- Decision Layer: `http://localhost:8000/health`
- Analysis Engine: `http://localhost:8090/health`

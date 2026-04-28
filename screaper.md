The Cursor Prompt
Role: You are a Senior DevOps Engineer and Systems Architect. Your mission is to build a high-performance, containerized Analysis Engine for the "OmniAegis" project.
Context:
Discovery Layer: We have a text-based crawler (main.py) that identifies URLs. It emits these to a Redis Stream (sentinel:ingest:stream).
Reasoning Layer: We have a sophisticated logic engine (pipeline.py) that performs graph-based reasoning and blockchain auditing to decide if an asset is infringing.
The Missing Link: We need to build the "Analysis Engine" that consumes the URLs from Redis, processes the media stream (video/audio), and identifies piracy using visual/audio fingerprinting.
Goal: Architect and implement a microservice that functions as the "Eyes" of the system.
Architectural Requirements:
Decoupled Ingestion Worker:
Implement an asynchronous worker that consumes from the sentinel:ingest:stream in Redis.
Use yt-dlp or ffmpeg integration to parse live stream manifests (.m3u8 / .dash) without downloading the entire stream.
Include a "Timeout-and-Abort" mechanism: If a stream isn't live within 10 seconds, drop the task to save resources (preventing worker starvation).
Multimodal Analysis Engine:
Implement a modular AnalysisService.
Use OpenCV + YOLOv8 (or similar) to detect official broadcaster logos, scoreboards, or watermarks.
Add a FingerprintService to perform perceptual hashing on video frames to compare against a known "Source of Truth" hash database.
Constraint: The analysis must be hardware-accelerated (use torch.device('cuda') if available, fallback to CPU).
Resilience & DevOps:
WAF Evasion: Implement a rotating Proxy/User-Agent middleware to prevent our scraper IPs from being blacklisted by streaming platforms.
Backpressure Handling: If the Decision Layer (pipeline.py) is slow, the Analysis Engine must implement a buffer (or circuit breaker) to avoid overwhelming the system.
Observability: Expose a /metrics endpoint using prometheus_client to track: 1. Streams scanned, 2. Piracy detections, 3. False positive rate, 4. Worker latency.
Integration Protocol:
Once the Analysis Engine confirms a match (e.g., >85% confidence score), it must NOT perform the audit itself.
Instead, it must push an AnalysisResult object to a new Redis stream (sentinel:decision:stream) which the existing pipeline.py should be updated to consume.
Deliverables:
A folder structure for the new analysis_engine service.
A Dockerfile optimized for multi-stage builds (keeping the image slim, despite the heavy AI dependencies).
The worker.py script that orchestrates the media parsing and analysis.
A docker-compose.override.yml snippet to link the new service with Redis and the existing backend.
Tone:
Strictly professional. Prioritize maintainability, testability, and "clean architecture" (Hexagonal/Ports & Adapters pattern). Use Python 3.11+.
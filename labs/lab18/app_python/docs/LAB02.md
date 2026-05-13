# Lab 2 — Docker Containerization

## 1. Docker Best Practices Applied

| Practice | Why it matters |
|----------|----------------|
| **Non-root user** | Reduces blast radius if the app or image is compromised; root inside container can be abused. |
| **Specific base version** (`python:3.13-slim`) | Reproducible builds; avoids surprise breakage when base image updates. |
| **Layer order** | Copy `requirements.txt` and run `pip install` before copying app code. Code changes then only invalidate the last layer; dependency layer is cached. |
| **Only copy necessary files** | Smaller build context and image; fewer secrets/artifacts in the image. |
| **`.dockerignore`** | Excludes dev/test/docs from build context → faster builds and no accidental inclusion of unneeded files. |
| **`EXPOSE 5000`** | Documents the port the app uses; doesn’t publish it (that’s `docker run -p`). |

**Snippet (layer order + non-root):**

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
# ...
USER appuser
```

## 2. Image Information & Decisions

- **Base:** `python:3.13-slim` — matches lab stack, smaller than full Python image, still has common libs (unlike alpine, which can cause build issues with some wheels).
- **Size:** Check with `docker images <your-image>` after build. Slim base keeps it moderate; no extra tools in the final layer.
- **Layers:** Base → user creation → WORKDIR → requirements copy + pip → app copy → chown → USER → EXPOSE/CMD. Dependency layer is reused when only code changes.

## 3. Build & Run Process

**Build:** (run from `app_python/`)

```
<paste your `docker build -t <name> .` output here>
```

**Run:**

```
<paste your `docker run -p 5000:5000 <name>` output here>
```

**Test endpoints:**

```
curl http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"89f830ea2369","platform":"Linux","platform_version":"Linux-6.17.0-12-generic-x86_64-with-glibc2.41","architecture":"x86_64","cpu_count":12,"python_version":"3.13.11"},"runtime":{"uptime_seconds":3,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T09:18:05.987481+00:00","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.14.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}

curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-04T09:18:08.395779+00:00","uptime_seconds":6}
```

**Docker Hub:**  
Repository URL: `https://hub.docker.com/r/woolfer0097kek/devops-course-lab2`

## 4. Technical Analysis

- **Why it works:** Uvicorn runs as `appuser`, binds to `0.0.0.0:5000` so the host can reach it when you use `-p`. Dependencies are installed in an earlier layer, so the app has FastAPI/uvicorn available.
- **Layer order:** If we copied everything first and then ran `pip install`, any change to `app.py` would invalidate the cache and re-run `pip install` every time. Putting dependencies first keeps installs cached.
- **Security:** Non-root user, minimal files in the image, no dev/test tooling. `.dockerignore` keeps `.git` and secrets out of the build context.
- **`.dockerignore`:** Reduces context sent to the daemon (faster `docker build`) and prevents `docs/`, `tests/`, `venv/`, `.git` from being considered for `COPY`, so they never end up in the image.

## 5. Challenges & Solutions

- I didn't encounter any serious challenges, because its quite routine task for me. However, i didn't really care about multi-stage building before this lab, but after comparisson I was quite impressed and will think about it in my work in future.

## 6. Multi-stage VS single
woolfer0097kek/devops-course-image-lab2-go   2.0        398779964a25   3 seconds ago    15MB
woolfer0097kek/devops-course-image-lab2      latest     9b3e60f18070   16 minutes ago   164MB

i wrote go dockerfile with multistage building strategy while python uses single-stage building
There is enourmous difference in its sizes! 15MB VS 164MB!
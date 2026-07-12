# DevOps Health Dashboard

A real-time system, CPU, memory, disk, network, and Docker monitoring dashboard built with **Flask**, **psutil**, and **Chart.js** — styled as a dark, glassmorphism, Grafana-inspired UI. Designed as a portfolio-ready, interview-ready DevOps project with production tooling: Docker, docker-compose, a Jenkins CI/CD pipeline, and a pytest test suite.

![Version](https://img.shields.io/badge/version-1.0.0-22d3ee)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [API Endpoints](#api-endpoints)
- [Installation (Local)](#installation-local)
- [Docker Commands](#docker-commands)
- [Docker Compose](#docker-compose)
- [Jenkins CI/CD](#jenkins-cicd)
- [AWS Deployment](#aws-deployment)
- [Running Tests](#running-tests)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)

---

## Features

- **Live metrics**, auto-refreshed every 2 seconds with no page reload
- System, CPU, memory, disk, network, Docker, and process monitoring
- Interactive Chart.js line charts for CPU / RAM / Disk / Network
- Health-based status badges (Healthy / Warning / Critical) with configurable thresholds
- Dark glassmorphism UI with light-mode toggle
- Process search, animated progress bars, toast notifications
- Downloadable PDF system report and JSON log snapshot
- Modular Flask architecture: Blueprints, service layer, utility layer, centralized logging
- Non-root Docker image with healthcheck, docker-compose stack, and a full Jenkins pipeline
- Pytest suite covering routes and service logic

## Architecture

```
                        ┌───────────────────────┐
                        │        Browser         │
                        │  (Bootstrap + Chart.js) │
                        └───────────┬─────────────┘
                                    │ fetch() every 2s
                                    ▼
                        ┌───────────────────────┐
                        │      Flask App         │
                        │  routes/views.py       │
                        │  routes/api.py         │
                        └───────────┬─────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ services/*.py   │ │ utils/*.py      │ │ Docker SDK      │
        │ (psutil-backed) │ │ formatters/log  │ │ (docker.sock)   │
        └────────────────┘ └────────────────┘ └────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │   Host OS /      │
        │   Container      │
        │   Kernel (psutil)│
        └────────────────┘
```

The app follows a **service-layer architecture**: routes stay thin and only handle HTTP concerns, while all metric-collection logic lives in `services/`, and shared helpers (formatting, logging) live in `utils/`.

## Folder Structure

```
health-dashboard/
├── app.py                  # Application factory & entrypoint
├── config.py                # Environment-driven configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── pytest.ini
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   └── index.html           # Single-page dashboard template
├── static/
│   ├── css/style.css        # Glassmorphism dark/light theme
│   ├── js/dashboard.js      # Fetch loop + DOM updates
│   ├── js/charts.js         # Chart.js configuration
│   └── images/
├── services/
│   ├── system_service.py
│   ├── cpu_service.py
│   ├── memory_service.py
│   ├── disk_service.py
│   ├── network_service.py
│   ├── docker_service.py
│   ├── process_service.py
│   ├── health_service.py
│   └── report_service.py    # PDF report generation
├── routes/
│   ├── views.py              # "/" and "/health"
│   └── api.py                 # All /api/* JSON endpoints
├── utils/
│   ├── logger.py
│   └── formatters.py
└── tests/
    ├── conftest.py
    ├── test_views.py
    ├── test_api.py
    └── test_services.py
```

## API Endpoints

| Method | Endpoint          | Description                                   |
|--------|-------------------|------------------------------------------------|
| GET    | `/`               | Renders the dashboard page                     |
| GET    | `/health`         | Liveness probe — `{"status": "ok"}`            |
| GET    | `/api/system`     | Hostname, IPs, OS, uptime, users, etc.         |
| GET    | `/api/cpu`        | CPU usage, per-core usage, frequency           |
| GET    | `/api/memory`     | RAM and swap usage                              |
| GET    | `/api/disk`       | Disk usage and mounted partitions               |
| GET    | `/api/network`    | Upload/download speed, interfaces               |
| GET    | `/api/docker`     | Docker version, containers, images, volumes     |
| GET    | `/api/processes`  | Top N processes (`?search=` `?limit=`)          |
| GET    | `/api/load`       | Load average + CPU temperature                  |
| GET    | `/api/summary`    | Aggregated dashboard summary + overall status   |
| GET    | `/api/report/pdf` | Downloads a PDF snapshot report                 |

Every endpoint returns JSON (except `/api/report/pdf`, which streams a PDF file).

## Installation (Local)

Requires Python 3.11+.

```bash
git clone https://github.com/your-username/health-dashboard.git
cd health-dashboard

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env             # adjust values as needed

python app.py                    # dev server on http://localhost:5000
```

For a production-like run locally:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 app:app
```

## Docker Commands

Build and run the image directly:

```bash
docker build -t devops-health-dashboard:latest .

docker run -d \
  --name devops-health-dashboard \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  devops-health-dashboard:latest
```

Check health status:

```bash
docker inspect --format='{{json .State.Health}}' devops-health-dashboard
```

> The Docker socket mount is **optional** — omit it if you don't want the dashboard to report on host containers/images/volumes. Without it, the Docker panel will show "unavailable" and the rest of the dashboard works normally.

## Docker Compose

```bash
cp .env.example .env
docker compose up -d --build

# View logs
docker compose logs -f dashboard

# Stop and remove
docker compose down
```

The compose file provisions the app container with a healthcheck, a named volume for logs, and an isolated bridge network.

## Jenkins CI/CD

The included `Jenkinsfile` defines an 8-stage pipeline:

1. **Checkout** — pulls source from SCM
2. **Install Dependencies** — creates a venv and installs `requirements.txt`
3. **Unit Tests** — runs `pytest` with JUnit XML reporting
4. **Build Docker Image** — tags with `${BUILD_NUMBER}` and `latest`
5. **Push to DockerHub** — uses Jenkins credential `dockerhub-credentials`
6. **Deploy** — recreates the running container
7. **Health Check** — polls `/health` until the app responds or times out
8. **Cleanup** — prunes dangling images and temporary files

**Setup:**
1. In Jenkins, add a "Username with password" credential named `dockerhub-credentials` with your DockerHub username/token.
2. Update `IMAGE_NAME` in the `Jenkinsfile` to your DockerHub namespace.
3. Create a Pipeline job pointing at this repository; Jenkins will pick up the `Jenkinsfile` automatically.

## AWS Deployment

A simple path to production on AWS:

1. **ECR** — push the built image to an Elastic Container Registry repository (`aws ecr get-login-password | docker login ...`, then `docker push`).
2. **ECS Fargate** — define a Task Definition using the ECR image, expose port 5000, and attach an Application Load Balancer with a target group healthcheck on `/health`.
3. **Secrets** — store `SECRET_KEY` and other environment variables in AWS Secrets Manager or SSM Parameter Store, injected into the ECS task definition (never hardcoded).
4. **Docker visibility** — Fargate does not expose a Docker socket, so the Docker panel will report "unavailable" in that environment; use an **EC2-backed ECS cluster** or a self-managed EC2 instance with the socket mounted if Docker container visibility is required.
5. **Scaling** — attach an Application Auto Scaling policy on CPU utilization for the ECS service.

## Running Tests

```bash
pip install -r requirements.txt
pytest
```

The suite covers:
- `/` and `/health` view routes
- All `/api/*` JSON endpoints (status codes, content types, expected keys)
- Service-layer unit tests (formatters, CPU/memory/disk/process services, health aggregation)

## Screenshots

> Add screenshots here after your first run:
>
> `docs/screenshots/overview.png` — Overview tab with summary cards and charts
> `docs/screenshots/processes.png` — Process table with live search
> `docs/screenshots/docker.png` — Docker containers panel
> `docs/screenshots/light-mode.png` — Light mode variant

## Future Improvements

- WebSocket-based push updates instead of polling, to reduce request overhead
- Historical metrics persistence (e.g. TimescaleDB/Prometheus) for trend analysis beyond the in-browser rolling window
- Role-based authentication for multi-user access
- Alerting integrations (Slack, PagerDuty, email) on status transitions
- Kubernetes manifests / Helm chart as an alternative to the Jenkins + Docker Compose flow
- GPU monitoring panel for ML/GPU workloads

---

Built with Flask, psutil, Docker SDK for Python, Bootstrap 5, and Chart.js.

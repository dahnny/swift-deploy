# SwiftDeploy

SwiftDeploy is a beginner-friendly DevOps project. Instead of writing Nginx and Docker Compose config by hand, you describe the stack once in `manifest.yaml`, then run `./swiftdeploy` to generate and manage everything.

The main idea is simple:

```text
manifest.yaml -> swiftdeploy -> nginx.conf + docker-compose.yml -> running stack
```

## Project Structure

```text
.
├── app/
│   ├── main.py
│   └── requirements.txt
├── templates/
│   ├── docker-compose.yml.tpl
│   └── nginx.conf.tpl
├── Dockerfile
├── README.md
├── manifest.yaml
└── swiftdeploy
```

## What Each Part Does

- `manifest.yaml` is the single source of truth.
- `swiftdeploy` is the CLI tool.
- `templates/` contains the config blueprints.
- `nginx.conf` is generated from the Nginx template.
- `docker-compose.yml` is generated from the Compose template.
- `app/` contains the FastAPI service.

## Requirements

Install these first:

- Docker Desktop or Docker Engine
- Docker Compose
- Python 3

## Setup

Make the CLI executable:

```bash
chmod +x swiftdeploy
```

Build the local app image:

```bash
docker build -t swift-deploy-1-node:latest .
```

This image name matches the required value in `manifest.yaml`.

## Manifest

The required base values are already included:

```yaml
services:
  image: swift-deploy-1-node:latest
  port: 3000

nginx:
  image: nginx:latest
  port: 8080

network:
  name: swiftdeploy-net
  driver_type: bridge
```

Extra beginner-friendly values are also included:

```yaml
services:
  mode: stable
  app_version: "1.0.0"

nginx:
  proxy_timeout: 10s
  contact: admin@example.com

restart_policy: unless-stopped
```

## Commands

### Generate Configs

```bash
./swiftdeploy init
```

This reads `manifest.yaml` and creates:

- `nginx.conf`
- `docker-compose.yml`

If the grader deletes those generated files, this command recreates them.

### Validate

```bash
./swiftdeploy validate
```

This runs five pre-flight checks:

- `manifest.yaml` exists and can be parsed
- required fields are present and not empty
- the app Docker image exists locally
- the Nginx host port is free
- generated `nginx.conf` passes `nginx -t`

Each check prints `PASS` or `FAIL`.

### Deploy

```bash
./swiftdeploy deploy
```

This:

1. runs `init`
2. starts the stack with Docker Compose
3. waits up to 60 seconds for `/healthz` to pass

Visit:

```bash
curl http://localhost:8080/
curl http://localhost:8080/healthz
```

The app port is not exposed directly. Traffic goes through Nginx on port `8080`.

### Promote to Canary

```bash
./swiftdeploy promote canary
```

This:

1. updates `services.mode` in `manifest.yaml`
2. regenerates `docker-compose.yml`
3. restarts only the app container
4. confirms `/healthz` reports canary mode

Check the canary header:

```bash
curl -i http://localhost:8080/healthz
```

You should see:

```text
X-Mode: canary
```

### Use Chaos Mode

Chaos only works in canary mode.

Slow responses:

```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode":"slow","duration":2}'
```

Random errors:

```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode":"error","rate":0.5}'
```

Recover:

```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode":"recover"}'
```

### Promote Back to Stable

```bash
./swiftdeploy promote stable
```

Stable mode disables canary-only chaos behavior.

### Teardown

```bash
./swiftdeploy teardown
```

This removes containers, the network, and volumes.

To also delete generated files:

```bash
./swiftdeploy teardown --clean
```

## Nginx Logs

Nginx writes access logs to the named Docker volume. To view them:

```bash
docker exec swiftdeploy-nginx cat /var/log/nginx/access.log
```

The log format is:

```text
$time_iso8601 | $status | ${request_time}s | $upstream_addr | $request
```

## Useful Demo Flow

Use this sequence for screenshots:

```bash
docker build -t swift-deploy-1-node:latest .
./swiftdeploy init
./swiftdeploy validate
./swiftdeploy deploy
curl http://localhost:8080/healthz
./swiftdeploy promote canary
curl -i http://localhost:8080/healthz
cat nginx.conf
cat docker-compose.yml
docker exec swiftdeploy-nginx cat /var/log/nginx/access.log
./swiftdeploy teardown --clean
```

## Beginner Explanation

Think of `manifest.yaml` as the recipe.

Think of `templates/` as reusable forms with blanks.

Think of `swiftdeploy` as the tool that fills in the blanks and then tells Docker what to run.

That is why the generated files should not be edited by hand. If you want to change the deployment, change `manifest.yaml`, then run:

```bash
./swiftdeploy init
```

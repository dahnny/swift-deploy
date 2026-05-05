services:
  app:
    image: {{SERVICE_IMAGE}}
    container_name: swiftdeploy-app
    restart: {{RESTART_POLICY}}
    environment:
      MODE: "{{MODE}}"
      APP_VERSION: "{{APP_VERSION}}"
      APP_PORT: "{{SERVICE_PORT}}"
    expose:
      - "{{SERVICE_PORT}}"
    networks:
      - swiftdeploy
    volumes:
      - swiftdeploy-logs:/var/log/swiftdeploy
    user: swiftdeploy
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:{{SERVICE_PORT}}/healthz', timeout=3)\""]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  nginx:
    image: {{NGINX_IMAGE}}
    container_name: swiftdeploy-nginx
    restart: {{RESTART_POLICY}}
    depends_on:
      app:
        condition: service_healthy
    ports:
      - "{{NGINX_PORT}}:{{NGINX_PORT}}"
    networks:
      - swiftdeploy
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - swiftdeploy-logs:/var/log/nginx
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
      - CHOWN
      - DAC_OVERRIDE
      - SETGID
      - SETUID
    security_opt:
      - no-new-privileges:true

networks:
  swiftdeploy:
    name: {{NETWORK_NAME}}
    driver: {{NETWORK_DRIVER}}

volumes:
  swiftdeploy-logs:
    name: swiftdeploy-logs

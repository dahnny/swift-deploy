events {}

http {
    log_format swiftdeploy '$time_iso8601 | $status | ${request_time}s | $upstream_addr | $request';
    access_log /var/log/nginx/access.log swiftdeploy;

    server {
        listen {{NGINX_PORT}};
        resolver 127.0.0.11 valid=10s ipv6=off;
        set $swiftdeploy_app "app:{{SERVICE_PORT}}";

        proxy_connect_timeout {{PROXY_TIMEOUT}};
        proxy_send_timeout {{PROXY_TIMEOUT}};
        proxy_read_timeout {{PROXY_TIMEOUT}};

        error_page 502 = /swiftdeploy_502.json;
        error_page 503 = /swiftdeploy_503.json;
        error_page 504 = /swiftdeploy_504.json;

        location / {
            proxy_pass http://$swiftdeploy_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            add_header X-Deployed-By swiftdeploy always;
            add_header X-Mode $upstream_http_x_mode always;
        }

        location = /swiftdeploy_502.json {
            internal;
            default_type application/json;
            return 502 '{"error":"bad_gateway","code":"502","service":"swiftdeploy","contact":"{{CONTACT}}"}';
        }

        location = /swiftdeploy_503.json {
            internal;
            default_type application/json;
            return 503 '{"error":"service_unavailable","code":"503","service":"swiftdeploy","contact":"{{CONTACT}}"}';
        }

        location = /swiftdeploy_504.json {
            internal;
            default_type application/json;
            return 504 '{"error":"gateway_timeout","code":"504","service":"swiftdeploy","contact":"{{CONTACT}}"}';
        }
    }
}

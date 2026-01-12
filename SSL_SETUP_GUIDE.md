# SSL/HTTPS 설정 가이드 - HTTP를 HTTPS로 변환

## 개요

FastAPI 애플리케이션을 HTTPS로 전환하는 여러 방법을 설명합니다.

---

## 방법 1: Render (현재 사용 중) ✅

**Render는 자동으로 HTTPS를 제공합니다!**

현재 배포된 `https://orders-2ch8.onrender.com`은 이미 HTTPS입니다.

### 장점
- ✅ 자동 SSL 인증서 관리
- ✅ 무료 HTTPS
- ✅ 자동 갱신
- ✅ 추가 설정 불필요

### 설정
별도 설정 없음. Render에 배포하면 자동으로 HTTPS URL이 제공됩니다.

---

## 방법 2: Nginx Reverse Proxy + Let's Encrypt (권장)

가장 일반적인 프로덕션 설정 방법입니다.

### 1. Nginx 설치

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 2. Nginx 설정 파일 생성

`/etc/nginx/sites-available/order-service`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # HTTP를 HTTPS로 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL 인증서 경로 (Certbot이 자동으로 설정)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # FastAPI 애플리케이션으로 프록시
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }

    # WebSocket 지원 (필요한 경우)
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Let's Encrypt 인증서 설치 (Certbot)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급 (자동으로 Nginx 설정도 업데이트)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

### 4. Nginx 활성화 및 재시작

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/order-service /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 5. FastAPI 애플리케이션 실행

```bash
# uvicorn은 HTTP로만 실행 (Nginx가 HTTPS 처리)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 방법 3: Caddy (가장 간단) 🚀

Caddy는 자동으로 SSL 인증서를 관리합니다.

### 1. Caddy 설치

```bash
# Ubuntu/Debian
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### 2. Caddyfile 생성

`/etc/caddy/Caddyfile`:

```
your-domain.com {
    reverse_proxy localhost:8000
}
```

### 3. Caddy 시작

```bash
sudo systemctl start caddy
sudo systemctl enable caddy
```

**끝!** Caddy가 자동으로 SSL 인증서를 발급하고 관리합니다.

---

## 방법 4: Cloudflare (무료 CDN + SSL)

### 1. Cloudflare 계정 생성 및 도메인 추가

1. [Cloudflare](https://cloudflare.com) 가입
2. 도메인 추가
3. DNS 레코드 설정 (A 레코드로 서버 IP 지정)

### 2. SSL/TLS 설정

Cloudflare Dashboard → SSL/TLS:
- **Encryption mode**: Full (strict) 선택
- 자동으로 HTTPS 제공

### 3. Nginx 설정 (Cloudflare IP 허용)

```nginx
# Cloudflare IP 범위만 허용 (선택사항)
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
# ... (전체 IP 범위는 Cloudflare 문서 참조)

real_ip_header CF-Connecting-IP;
```

---

## 방법 5: uvicorn에서 직접 SSL 설정

**주의**: 프로덕션에서는 권장하지 않습니다. Reverse proxy 사용을 권장합니다.

### 1. SSL 인증서 준비

```bash
# Let's Encrypt로 인증서 발급
sudo certbot certonly --standalone -d your-domain.com
```

### 2. uvicorn 실행

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile /etc/letsencrypt/live/your-domain.com/privkey.pem \
    --ssl-certfile /etc/letsencrypt/live/your-domain.com/fullchain.pem
```

### 3. 코드에서 설정 (선택사항)

`app/config.py`에 SSL 설정 추가:

```python
ssl_keyfile: str | None = Field(default=None, description="SSL key file path")
ssl_certfile: str | None = Field(default=None, description="SSL certificate file path")
```

---

## 방법 6: Docker + Traefik (컨테이너 환경)

### docker-compose.yml 예제

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}

  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    labels:
      - "traefik.http.routers.app.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.app.entrypoints=websecure"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"
      - "traefik.http.services.app.loadbalancer.server.port=8000"
```

---

## 비교표

| 방법 | 난이도 | 비용 | 자동 갱신 | 권장도 |
|------|--------|------|-----------|--------|
| Render | ⭐ 매우 쉬움 | 무료 | ✅ 자동 | ✅ 현재 사용 중 |
| Nginx + Let's Encrypt | ⭐⭐ 보통 | 무료 | ✅ 자동 | ✅ 프로덕션 권장 |
| Caddy | ⭐ 매우 쉬움 | 무료 | ✅ 자동 | ✅ 간단한 설정 |
| Cloudflare | ⭐⭐ 보통 | 무료 | ✅ 자동 | ✅ CDN 필요 시 |
| uvicorn 직접 | ⭐⭐⭐ 어려움 | 무료 | ❌ 수동 | ❌ 권장 안 함 |
| Traefik | ⭐⭐ 보통 | 무료 | ✅ 자동 | ✅ Docker 환경 |

---

## 현재 프로젝트 권장사항

### 이미 Render 사용 중인 경우
✅ **추가 작업 불필요!** Render가 이미 HTTPS를 제공합니다.

### 자체 서버로 이전하는 경우
1. **개발/테스트**: Caddy 사용 (가장 간단)
2. **프로덕션**: Nginx + Let's Encrypt (가장 안정적)

---

## SSL 인증서 갱신

### Let's Encrypt (Certbot)

```bash
# 수동 갱신
sudo certbot renew

# 자동 갱신 설정 (cron)
sudo crontab -e
# 다음 줄 추가:
0 0 * * * certbot renew --quiet
```

### Caddy
자동으로 갱신됩니다. 추가 작업 불필요.

---

## HTTP → HTTPS 리다이렉트

### Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Caddy
자동으로 처리됩니다.

---

## 문제 해결

### SSL 인증서 오류
- 도메인이 서버 IP를 가리키는지 확인
- 방화벽에서 80, 443 포트 열기
- Certbot 로그 확인: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`

### Mixed Content 오류
- 모든 리소스를 HTTPS로 로드
- `Content-Security-Policy` 헤더 설정

---

## 보안 체크리스트

- [ ] HTTPS 강제 리다이렉트 설정
- [ ] HSTS 헤더 설정
- [ ] 최신 TLS 버전 사용 (1.2 이상)
- [ ] 강력한 암호화 알고리즘 사용
- [ ] SSL 인증서 자동 갱신 설정
- [ ] 보안 헤더 설정 (CSP, X-Frame-Options 등)

---

## 참고 자료

- [Let's Encrypt](https://letsencrypt.org/)
- [Certbot 문서](https://certbot.eff.org/)
- [Nginx SSL 설정](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Caddy 문서](https://caddyserver.com/docs/)
- [Cloudflare SSL](https://developers.cloudflare.com/ssl/)


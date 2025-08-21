# Campus Helpdesk AI

Hệ thống hỗ trợ sinh viên thông minh sử dụng kiến trúc Multi-Agent, được thiết kế để giải quyết các vấn đề và yêu cầu thường gặp của sinh viên một cách hiệu quả.

## Kiến trúc Triển khai (Production Architecture)

Kiến trúc triển khai được thiết kế để hoạt động trên một máy chủ duy nhất sử dụng Docker Compose, bao gồm 3 services chính:

-   **Frontend Service**:
    -   Sử dụng image `nginx:stable-alpine` để phục vụ giao diện người dùng (React + Vite).
    -   Hoạt động như một reverse proxy, chuyển tiếp tất cả các request API (`/api/*`) đến Backend Service.
    -   Chịu trách nhiệm xử lý các request từ client ở cổng `80`.

-   **Gateway Service (Backend)**:
    -   Ứng dụng FastAPI chịu trách nhiệm điều phối hệ thống multi-agent.
    -   Xử lý logic nghiệp vụ, giao tiếp với các mô hình ngôn ngữ (LLM).
    -   Kết nối với Redis để lưu trữ và truy xuất lịch sử trò chuyện.
    -   Lắng nghe các request từ Frontend ở cổng `8000`.

-   **Redis Service**:
    -   Cơ sở dữ liệu in-memory dùng để quản lý session và lưu trữ lịch sử chat.

### Luồng Request

```mermaid
flowchart TD
  %% --- Groups ---
  subgraph Client
    U[User<br/>(Browser)]
  end

  subgraph "Docker Host / Compose"
    FE[A. Frontend Container<br/>Nginx<br/><small>serve static at “/”</small>]
    GW[B. Gateway Container<br/>FastAPI]
    R[(C. Redis)]
  end

  subgraph External
    LLM[External LLM<br/>(e.g., Google&nbsp;Gemini)]
  end

  %% --- Edges ---
  U -- "HTTPS (443)" --> FE
  FE -- "/api/* (reverse proxy)" --> GW
  GW <--> R
  GW -- "LLM API" --> LLM

  %% --- Styles ---
  classDef client fill:#E3F2FD,stroke:#1E88E5,color:#0D47A1
  classDef service fill:#E8F5E9,stroke:#43A047,color:#1B5E20
  classDef cache fill:#FFF8E1,stroke:#F9A825,color:#E65100
  classDef external fill:#F3E5F5,stroke:#8E24AA,color:#4A148C

  class U client
  class FE, GW service
  class R cache
  class LLM external

```

## Hướng dẫn Triển khai (Deployment)

Quy trình này tập trung vào việc build các Docker image ở môi trường local, đẩy chúng lên một container registry (như Docker Hub), và sau đó triển khai trên một máy chủ production.

### Yêu cầu hệ thống

-   **Local Machine**: Docker đã được cài đặt.
-   **Server**: Docker và Docker Compose đã được cài đặt.
-   **Container Registry**: Một tài khoản Docker Hub hoặc registry tương tự.

---

### Bước 1: Build và Đẩy Docker Images (Thực hiện ở Local)

#### 1.1. Build Frontend Image

Di chuyển vào thư mục frontend và chạy lệnh build:

```bash
cd intel-campus-ai-main
docker build -t your-dockerhub-username/campus-helpdesk-frontend:latest .
```
*(Lưu ý: Thay `your-dockerhub-username` bằng tên tài khoản Docker Hub của bạn)*

#### 1.2. Build Backend Image

Quay lại thư mục gốc của dự án. Backend được build từ một Dockerfile cơ sở.

```bash
cd ..
docker build -f services/bases/Dockerfile --build-arg SERVICE_DIR=services/gateway -t your-dockerhub-username/campus-helpdesk-backend:latest .
```
*(Lưu ý: Thay `your-dockerhub-username` bằng tên tài khoản Docker Hub của bạn)*

#### 1.3. Đẩy Images lên Registry

Sau khi build thành công, hãy đăng nhập và đẩy cả hai image lên.

```bash
docker login
docker push your-dockerhub-username/campus-helpdesk-frontend:latest
docker push your-dockerhub-username/campus-helpdesk-backend:latest
```

---

### Bước 2: Cấu hình và Chạy trên Server

#### 2.1. Chuẩn bị Server

SSH vào server của bạn và tạo một thư mục để chứa các file cấu hình.

```bash
mkdir campus-helpdesk-deploy
cd campus-helpdesk-deploy
```

#### 2.2. Tạo file `docker-compose.yml`

Tạo một file tên là `docker-compose.yml` (`nano docker-compose.yml`) và dán nội dung sau vào:

```yaml
services:
  frontend:
    image: your-dockerhub-username/campus-helpdesk-frontend:latest
    ports:
      - "80:80"
    restart: unless-stopped
    networks:
      - campus-net-simple
    depends_on:
      - gateway

  gateway:
    image: your-dockerhub-username/campus-helpdesk-backend:latest
    restart: unless-stopped
    environment:
      # Các biến môi trường sẽ được đọc từ file .env
      LLM_PROVIDER: ${LLM_PROVIDER}
      LLM_MODEL: ${LLM_MODEL}
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      REDIS_URL: redis://redis:6379/0
      # Các URL cho các service khác (nếu có)
      GATEWAY_PORT: 8000
      POLICY_URL: http://policy:8000
      TICKET_URL: http://ticket:8000
      ACTION_URL: http://action:8000
      ESCALATION_URL: http://escalation:8000
    networks:
      - campus-net-simple

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - campus-net-simple

networks:
  campus-net-simple:
    driver: bridge
```
*(Quan trọng: Hãy thay `your-dockerhub-username` bằng tên tài khoản Docker Hub của bạn trong file này)*

#### 2.3. Tạo file `.env`

Tạo file `.env` (`nano .env`) để chứa các thông tin nhạy cảm. Đây là một ví dụ:

```env
# Cấu hình LLM
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash

# API Keys
GOOGLE_API_KEY=your_google_api_key_here
```

#### 2.4. Khởi động hệ thống

Chạy lệnh sau để kéo các image về và khởi động tất cả các services.

```bash
docker compose up -d
```

Ứng dụng của bạn bây giờ sẽ có thể truy cập được thông qua địa chỉ IP public của server.

---

### Bước 3: Cập nhật hệ thống

Khi bạn có thay đổi ở mã nguồn (frontend hoặc backend), hãy lặp lại **Bước 1** (build và push image mới). Sau đó, trên server, chỉ cần chạy lệnh:

```bash
# Di chuyển vào thư mục campus-helpdesk-deploy
docker compose pull
docker compose up -d
```

Lệnh này sẽ kéo các phiên bản image mới nhất về và khởi động lại các services cần thiết một cách mượt mà.

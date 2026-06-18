# HC-Inventory — 수출 비용 계산기 (독립 사이트)

대시보드(WONGI/export_calculator)의 **계산기 모듈**을 떼어낸 **완전 독립** 사이트.
런타임 의존 0 (자체 백엔드 + 자체 DB). 외부 거래처용 단일 계정.

## 구성

| | 스택 | 위치 |
|---|---|---|
| 백엔드 | Django + DRF | `backend/` |
| 프론트 | Next.js standalone | `frontend/` (P6 — 작업 예정) |

## 백엔드 (`backend/`)

- `hc_calc/` — 계산 모델(21) + 계산 로직(services) + 계산 3API + 계산이력 조회
- `hc_auth/` — 단일 계정(HC) 세션 인증 + 초기PW 강제변경
- `hc_project/` — settings(화이트리스트) / urls / wsgi

### API
- `POST /api/calculate_costs/` — 수출 비용 계산
- `GET  /api/amazon-categories/` · `GET /api/walmart-categories/`
- `GET  /api/calculation-logs/` — 계산 이력(단일계정 전체)
- `POST /auth/login/` · `/auth/logout/` · `GET /auth/session/status/` · `POST /auth/change-password/`
- 전역 `IsAuthenticated`(로그인/세션상태만 공개). 단일 계정이라 권한 시스템 없음.

### 로컬 실행 (sqlite)
```bash
cd backend
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
export HC_DB_ENGINE=sqlite
.venv/bin/python manage.py migrate
.venv/bin/python manage.py create_hc_user          # HC / 123456 (첫 로그인 강제변경)
.venv/bin/python manage.py runserver
```

### 데이터 이관 (운영 → 신규 DB, 1회)
```bash
# 운영 EC2: 계산 기준 데이터 dump (summary / CalculationLog 제외)
dumpdata calculations.VariableConfigurations calculations.Amazon* ... > seed_raw.json
sed 's/"model": "calculations\./"model": "hc_calc./g' seed_raw.json > seed/calc_seed.json
# 신규 DB 적재 (signal 이중적재 차단 + summary 재계산)
python manage.py seed_calc_data seed/calc_seed.json
```

## 배포 (같은 EC2, 기존 시스템과 완전 분리)
- 디렉토리 `/home/ubuntu/hc-calculator/` (WONGI sync 범위 밖)
- 포트 Next 3005 / Django 8010 / 전용 postgres 5434
- systemd `hc-calc-backend` / `hc-calc-frontend`, nginx 별 server block(새 도메인)
- 상세: 구현 계획서 `DATA/DEV/sop/spec/hc_inventory_calculator_clone_plan_v1_2026_06_18.md`

## 보안
- public repo — 시크릿은 전부 env(`.env.example` 참조), 하드코딩 0
- 단일 계정 HC, 초기 PW 첫 로그인 강제변경, nginx rate-limit, HTTPS/HSTS/secure cookie

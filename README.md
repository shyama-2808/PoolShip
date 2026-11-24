# PoolShip 🚛🌱
> **Peer-to-Peer Freight Pooling Platform for Small Businesses & Transporters**

PoolShip is a digital logistics platform where businesses shipping goods along similar highway corridors share truck capacity and split the cost transparently. It addresses India's **₹1,00,000 crore part-truckload (PTL) gap** for MSMEs, cutting freight spend by 30–50% while reducing empty cargo space, fuel burn, and carbon emissions.

---

## 🏗️ Architecture & Tech Stack

```
PoolShip/
├── backend/                   # Python (FastAPI) Optimization Engine & REST API
│   ├── app/
│   │   ├── api/v1/            # API endpoints (auth, shipments, trucks, pools, tracking, analytics)
│   │   ├── core/              # Config, JWT auth, environment settings
│   │   ├── db/                # PostgreSQL + PostGIS session engine
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Core Algorithms (Bin-packing, Cost split, CO2, Corridors)
│   ├── tests/                 # Unit tests for capacity and cost-splitting math
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                  # Next.js 15 (TypeScript) + Tailwind CSS
│   ├── src/
│   │   ├── app/               # Next.js App Router (Landing, Shipper, Transporter, Admin, Tracking)
│   │   ├── components/        # UI & Layout components
│   │   ├── lib/               # API clients & utilities
│   │   └── types/             # TypeScript definitions
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml         # Turnkey PostgreSQL/PostGIS, FastAPI & Next.js orchestration
└── README.md
```

### Why this Tech Stack?
* **Python (FastAPI):** Logistics is fundamentally mathematical. Python provides the best ecosystem for operations research:
  * **Bin-packing / Capacity Optimizer:** 3D and 1D Best-Fit-Decreasing load consolidation.
  * **Vehicle Routing & Corridors:** Great-circle cross-track corridor detection and OSRM integration.
  * **Cost-Splitting:** Ton-kilometer ($\text{Ton} \times \text{Km}$) proportional allocation model.
  * **Carbon Savings:** DEFRA/EPA standard diesel truck emission modeling.
* **Next.js 15 (React 19, TypeScript, Tailwind):** Fast, modern, responsive multi-role UI for Shippers, Transporters, and Admins.
* **PostgreSQL + PostGIS:** Industry standard for spatial indexing and highway corridor geometry queries (`ST_DWithin`, `ST_Buffer`).

---

## 🚀 Quickstart

### Option 1: Run with Docker Compose (Recommended)
Make sure Docker is running, then execute:

```bash
docker-compose up --build
```

* **Frontend:** [http://localhost:3000](http://localhost:3000)
* **Backend API Docs (Swagger):** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
* **PostgreSQL/PostGIS:** `localhost:5432`

---

### Option 2: Run Locally (Bare-metal)

#### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run FastAPI dev server
uvicorn app.main:app --reload --port 8000
```

#### 2. Run Algorithmic Tests
```bash
cd backend
pytest tests/
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Visit [http://localhost:3000](http://localhost:3000).

---

## 📋 Build Phases & Roadmap (from Feature Specification)

- [x] **Project Scaffolding & Initial Architecture**
- [ ] **Phase 1: MVP Core**
  - [x] Data models & schemas (Users, Shipments, Trucks, Pools, Tracking)
  - [x] Load consolidation / Bin-packing algorithm (`capacity_optimizer.py`)
  - [x] Fair ton-km cost splitting algorithm (`cost_splitter.py`)
  - [x] Corridor route matching logic (`route_matching.py`)
  - [x] Shipper posting & Transporter listing dashboards
- [ ] **Phase 2: Demo Polish**
  - [x] Interactive simulator on landing page
  - [x] Carbon savings & fuel calculator (`carbon_calculator.py`)
  - [ ] Leaflet / MapLibre interactive route polylines & waypoint visualization
- [ ] **Phase 3: Smart Features**
  - [ ] Multi-stop VRP sequencing with Google OR-Tools / OSRM
  - [x] Hazardous / perishable goods compatibility matrix
  - [x] Empty-return-trip matching indicator
- [ ] **Phase 4: Trust & Business Extras**
  - [x] GSTIN verification queue
  - [x] Digital Proof of Delivery (POD) with OTP release flow
  - [ ] PDF invoice and e-way bill generation

---

## 📄 License
MIT


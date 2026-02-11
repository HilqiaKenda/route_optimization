# ⛽ Route Optimization API

Find the cheapest fuel stops along a driving route between two addresses.

This API calculates a driving route using OpenRouteService (ORS) and intelligently finds fuel stations from a CSV dataset that lie close to the route — returning the cheapest stations along the way.

## 🔧 Built With

- Django + Django REST Framework
- Redis (caching)
- OpenRouteService (routing + geocoding)
- Pandas (CSV ingestion)
- In-memory spatial filtering (bounding boxes)

---

## 🚀 What It Does

### Request

```json
{
  "start_address": "Texas",
  "end_address": "New York"
}
```

### Response

```json
{
  "distance_miles": 0.93,
  "fuel_stops": [
    {
      "name": "KWIK TRIP #796",
      "price": 3.28,
      "lat": 43.978,
      "lon": -90.504
    }
  ],
  "total_fuel_cost": 3.28,
  "start_address": [-71.0681257, 42.3547681],
  "end_address": [-71.075124, 42.3491677],
  "pois": [
    {
      "name": "Unknown",
      "latitude": 42.35542,
      "longitude": -71.069394,
      "categories": ["bench"],
      "website": "",
      "opening_hours": ""
    }
  ]
}
```

### ⚙️ Setup

#### 1. Install Dependencies

```bash
pip install django djangorestframework pandas requests redis
```

### 🏗️ Architecture

Client
↓
Django API
↓
Geocode (ORS) → Cache forever (Redis)
↓
Route (ORS)
↓
Bounding Box Corridor
↓
Match CSV stations (Pandas in memory)
↓
Return cheapest stations

### 📁 Project Structure

core/
├── utils/
│ ├── fuel_loader.py
│ ├── geocode.py
│ ├── openroute.py
│ └── optimizer.py
├── views.py
├── urls.py

fuel_route/
└── settings.py
├── .gitignore
├── fuel-prices-for-be-assessment.csv
├── LICENSE
├── manage.py
├── README.md
└── requirements.txt

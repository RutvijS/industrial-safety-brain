# Datasets — Industrial Safety Brain

Synthetic but realistic datasets for a virtual steel plant with 4 operational zones.

## Plant Layout

| Zone | Name | Primary Risk |
|------|------|-------------|
| Zone A | Coke Oven Area | High Gas Risk |
| Zone B | Boiler House | High Temperature |
| Zone C | Maintenance Workshop | Frequent Hot Work |
| Zone D | Chemical Storage | Hazardous Chemicals |

---

## Datasets

### 1. `sensors/sensors.json` (~500 records)

Real-time sensor readings from equipment across all zones.

| Field | Type | Description |
|-------|------|-------------|
| `sensor_id` | string | Unique reading ID (SEN-0001) |
| `timestamp` | ISO-8601 | When the reading was taken |
| `zone` | string | Zone A–D |
| `equipment` | string | Equipment that generated the reading |
| `gas_level` | float | Gas concentration in ppm |
| `temperature` | float | Temperature in °C |
| `pressure` | float | Pressure in bar |
| `humidity` | float | Relative humidity in % |
| `vibration` | float | Vibration in mm/s |
| `status` | string | Normal / Warning / Critical |

**Correlations:** High gas → elevated temperature. Boiler zone → higher pressure. ~15% readings are dangerous.

---

### 2. `permits/permits.json` (~100 records)

Work permit records (Permit to Work system).

| Field | Type | Description |
|-------|------|-------------|
| `permit_id` | string | Unique permit ID (PTW-0001) |
| `permit_type` | string | Hot Work / Confined Space Entry / Electrical Isolation / Maintenance |
| `zone` | string | Where the work occurs |
| `equipment` | string | Target equipment |
| `issued_to` | string | Worker name |
| `approved_by` | string | Supervisor name |
| `start_time` | ISO-8601 | Permit validity start |
| `end_time` | ISO-8601 | Permit validity end |
| `status` | string | Approved / Closed / Expired / Revoked / Pending |

**Correlations:** Hot Work → mostly Zone C. Confined Space → mostly Zone A.

---

### 3. `maintenance/maintenance.json` (~100 records)

Equipment maintenance work orders.

| Field | Type | Description |
|-------|------|-------------|
| `maintenance_id` | string | Unique ID (MNT-0001) |
| `equipment` | string | Target equipment |
| `zone` | string | Equipment zone |
| `maintenance_type` | string | Preventive / Corrective / Emergency / Inspection |
| `assigned_engineer` | string | Worker assigned |
| `status` | string | Completed / In Progress / Scheduled / Overdue / Cancelled |
| `scheduled_time` | ISO-8601 | When maintenance is planned |
| `completion_time` | ISO-8601 or null | When completed |
| `remarks` | string | Type-appropriate notes |

---

### 4. `shifts/shifts.json` (~360 records)

Shift schedules for all zones over 30 days.

| Field | Type | Description |
|-------|------|-------------|
| `shift_id` | string | Unique ID (SHF-0001) |
| `shift_name` | string | Morning / Evening / Night |
| `supervisor` | string | Supervisor name |
| `supervisor_id` | string | Supervisor ID |
| `workers` | array | Worker names assigned |
| `worker_ids` | array | Worker IDs assigned |
| `start_time` | ISO-8601 | Shift start |
| `end_time` | ISO-8601 | Shift end |
| `zone` | string | Zone assignment |

---

### 5. `incidents/incidents.json` (~50 records)

Historical safety incidents over ~18 months.

| Field | Type | Description |
|-------|------|-------------|
| `incident_id` | string | Unique ID (INC-0001) |
| `date` | ISO-8601 | When it happened |
| `zone` | string | Where it happened |
| `equipment` | string | Equipment involved |
| `description` | string | What happened |
| `root_cause` | string | Why it happened |
| `severity` | string | Minor / Moderate / Serious / Critical / Fatal |
| `injuries` | integer | Number of injuries |
| `corrective_action` | string | What was done to fix it |
| `lessons_learned` | string | Prevention takeaway |
| `related_regulation` | string | OSHA or ASME reference |

**Correlations:** Gas leaks → Zone A. Pressure surges → Zone B. Hot work fires → Zone C. Chemical spills → Zone D. ~25% occur near shift changes.

---

## Regenerating Datasets

```bash
cd industrial-safety-brain
python scripts/generate_all.py
```

All data is seeded (`RANDOM_SEED = 42`) — re-running produces identical output.

### Individual generators

```bash
python scripts/generate_sensor_data.py
python scripts/generate_permits.py
python scripts/generate_maintenance.py
python scripts/generate_shifts.py
python scripts/generate_incidents.py
```

### Validation only

```bash
python scripts/validate_data.py
```

---

## Future Use

These datasets are designed to power:

- **Compound Risk Detection** — correlate sensor + permit + maintenance gaps
- **RAG** — feed incidents and regulations into retrieval-augmented generation
- **Knowledge Graph** — link equipment → zone → incidents → regulations
- **Safety Copilot** — context-aware AI using live sensor + historical data
- **Dashboard & Heatmap** — visualise risk by zone, time, and equipment
- **Incident Intelligence** — predict similar incidents from patterns
- **Emergency Response** — auto-generate response plans from incident history

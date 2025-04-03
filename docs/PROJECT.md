# Senior Backend Engineer - ISW | Take Home

## Overview

This backend service is designed to manage calibrations of a hardware device. Each calibration includes:

- `calibration_type`
- `value`
- `timestamp`
- `username`

Calibrations can be tagged with arbitrary strings to describe different states of a device. Tags can be added or removed
from calibrations, and the tagging history is preserved.

## Technology Stack

- **Language:** Python
- **Database:** PostgreSQL or SQLite
- **Libraries:** See: `pyproject.toml`

---

## Use Cases & API Endpoints

### 1. Create a New Calibration

**Use Case:** `AddCalibrationUseCase`  [application.use_cases.calibrations.add_calibration.py](src/application/use_cases/calibrations/add_calibration_use_case.py)

**Endpoint:** `POST /calibrations`

**Input:**

```json
{
  "calibration_type": "string",
  "value": "float",
  "timestamp": "string (ISO 8601)",
  "username": "string"
}
```

**Output:**

```json
{
  "calibration_id": "uuid"
}
```

---

### 2. Query Calibrations by Filter `list_calibrations_use_case`

**Use Case:** `ListCalibrationsUseCase`  [application.use_cases.calibrations.list_calibrations.py](src/application/use_cases/calibrations/list_calibrations.py)

**Endpoint:** `GET /calibrations`

**Query Parameters:**

- `username`: `string`
- `timestamp`: `string (ISO 8601)`
- `calibration_type`: `string`

**Output:**

```json
[
  {
    "calibration_id": "uuid",
    "calibration_type": "string",
    "value": "float",
    "timestamp": "string (ISO 8601)",
    "username": "string"
  }
]
```

---

### 3. Tagging Support

#### 3a. Add a tag to a Calibration

**Use Case:** `AddTagToCalibrationUseCase`  [application.use_cases.tags.add_tag_to_calibration.py](src/application/use_cases/tags/add_tag_to_calibration.py)

**Endpoint:** `POST /calibrations/{calibration_id}/tags`

**Input:**

```json
{
  "tag": "string"
}
```

**Output:**

- body
  ```json
  {
    "message": "Tag added successfully"
  }
  ```

#### 3b. Removing a tag

**Use Case:** `RemoveTagFromCalibrationUseCase` [application.use_cases.tags.remove_tag_from_calibration.py](src/application/use_cases/tags/remove_tag_from_calibration.py)

**Endpoint:** `DELETE /calibrations/{calibration_id}/tags/{tag_name}` [application.use_cases.tags.remove_tag_from_calibration](src/application/use_cases/tags/remove_tag_from_calibration.py)

**Input:**

- path: `tag`

**Output:**

- body:
  ```json
  {
    "message": "Tag removed successfully"
  }
  ```

**Notes:**

- Each calibration can be tagged and untagged with any number of tags
- Each tag is an arbitrary string i.e. the tags are not pre-defined (examples: `"current-state"`, `"baseline-2025"`)
- Whenever a calibration is tagged or untagged those times are recorded

---

### 4. Retrieve Calibrations by Tag

**Use Case**: `GetCalibrationsByTagUseCase` - [application.use_cases.tags.get_calibrations_by_tag.py](src/application/use_cases/tags/get_calibrations_by_tag.py)

**Endpoint:** `GET /tags/{tag}/calibrations`

**Query Parameters:**

- `timestamp`: `string (ISO 8601)`
- `username`: `string`

**Output:**

- body
  - # TODO: (docs): add Response Schema

**Notes:**

- Output: The list of calibrations associated with that tag at that time (i.e.,
  calibrations added to the tag at or before that time, and not removed before that time)

---

### 5. Query Tags Associated with a Calibration

**Use Case**: `GetTagsForCalibrationUseCase` - [application.use_cases.calibrations.get_tags_for_calibration.py](application/use_cases/calibrations/get_tags_for_calibration.py)

**Endpoint:** `GET /calibrations/{calibration_id}/tags`

**Query Parameters:**

- `timestamp`: `string (ISO 8601)`

**Output:**

```json
[
  "tag1",
  "tag2",
  "tag3"
]
```

**Notes:**

- Given a calibration primary key and a timestamp, retrieve all the tags that it was a
  part of at that time

---

## Sample Calibration Data

```json
[
  {
    "calibration_type": "offset",
    "value": 1.0,
    "username": "alice"
  },
  {
    "calibration_type": "gain",
    "value": 1.5,
    "username": "bob"
  },
  {
    "calibration_type": "temperature",
    "value": -0.3,
    "username": "charlie"
  },
  {
    "calibration_type": "offset",
    "value": 0.9,
    "username": "alice"
  },
  {
    "calibration_type": "gain",
    "value": 1.6,
    "username": "dana"
  },
  {
    "calibration_type": "offset",
    "value": 1.2,
    "username": "bob"
  },
  {
    "calibration_type": "gain",
    "value": 1.55,
    "username": "alice"
  },
  {
    "calibration_type": "temperature",
    "value": -0.1,
    "username": "charlie"
  },
  {
    "calibration_type": "pressure",
    "value": 101.3,
    "username": "dana"
  },
  {
    "calibration_type": "offset",
    "value": 1.1,
    "username": "alice"
  },
  {
    "calibration_type": "gain",
    "value": 1.4,
    "username": "bob"
  },
  {
    "calibration_type": "offset",
    "value": 1.3,
    "username": "charlie"
  },
  {
    "calibration_type": "temperature",
    "value": -0.2,
    "username": "alice"
  },
  {
    "calibration_type": "pressure",
    "value": 100.8,
    "username": "bob"
  },
  {
    "calibration_type": "gain",
    "value": 1.6,
    "username": "charlie"
  }
]
```

---

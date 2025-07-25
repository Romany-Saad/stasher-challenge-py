# ⚡ ⚡ ⚡
## To keep this document intact, solution docs were added [here](SOLUTION.md). 
# ⚡ ⚡ ⚡ 

# Stasher Backend Interview Challenge

Welcome to the Stasher backend interview challenge! This project is a simplified version of our bag storage platform, where travelers can find locations to store their luggage.

## Task Overview

Your task is to implement a search feature that allows users to find available stashpoints (bag storage locations) based on:

- Location (latitude/longitude)
- Desired drop-off and pick-up times
- Number of bags to store

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your machine
- Git

### Setup

1. Clone this repository
2. Navigate to the project directory
3. Start the application using Docker Compose:

```bash
docker-compose up -d
```

4. The API will be available at `http://localhost:5000`
5. You can verify it's running with:

```bash
curl http://localhost:5000/healthcheck
```

## The Challenge

### Current Functionality

The application already has basic functionality:

- A Stashpoint model that represents bag storage locations
- A Booking model to track bag storage reservations
- An endpoint to list all stashpoints at `/api/v1/stashpoints/`
- Database with test data pre-populated

### Your Task

You need to enhance the stashpoints endpoint to allow filtering by availability. The endpoint should:

1. Accept the following query parameters:

   - `lat` (float): Latitude for the search location
   - `lng` (float): Longitude for the search location
   - `dropoff` (ISO datetime): When the user wants to drop off their bags
   - `pickup` (ISO datetime): When the user wants to pick up their bags
   - `bag_count` (integer): Number of bags to store
   - `radius_km` (float, optional): Search radius in kilometers

2. Return only stashpoints that:

   - Are within the specified radius of the coordinates
   - Have enough capacity for the requested number of bags during the specified time period
   - Are open during the requested drop-off and pick-up times

3. Results should be ordered by distance from the search coordinates

### Example Request

```
GET /api/v1/stashpoints/?lat=51.5074&lng=-0.1278&dropoff=2023-04-20T10:00:00Z&pickup=2023-04-20T18:00:00Z&bag_count=2&radius_km=5
```

### Response Format

The response should be a JSON array of available stashpoints, with each stashpoint containing at least:

```json
[
  {
    "id": "abc123",
    "name": "Central Cafe Storage",
    "address": "123 Main Street",
    "latitude": 51.5107,
    "longitude": -0.1246,
    "distance_km": 0.5,
    "capacity": 20,
    "available_capacity": 15,
    "open_from": "08:00",
    "open_until": "22:00"
  },
  ...
]
```

## Evaluation Criteria

We'll evaluate your solution based on:

- Correctness: Does it return the correct stashpoints?
- Code quality: Is your code clean and well-organized?
- Edge cases: How does your solution handle edge cases?
- Performance: How efficient is your solution?

## Submission

When you're ready, send us your solution as a Git repository. Make sure to include instructions for running your solution if they differ from the above.

You may also submit a README.md to accompany your solution, to explain any decisions made or enhancements you would make with more time.

Good luck!

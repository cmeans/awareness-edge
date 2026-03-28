# awareness-edge — bridge between your systems and AI awareness
# Copyright (C) 2026 Chris Means
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""GPS receiver — accepts location updates from Tasker via HTTP POST.

Writes each location update to mcp-awareness as an add_context entry.
Full breadcrumb retention by default (every data point stored, not just latest).

Run standalone:
    python -m awareness_edge.receivers.gps

Tasker HTTP Request action:
    Method: POST
    URL: http://<laptop-ip>:8421/location
    Headers: Content-Type: application/json
    Body: {"lat": %LOCN, "lon": %LOCLO, "accuracy": %LOCACC, "speed": %LOCSPD, "battery": %BATT}

Environment variables:
    AWARENESS_URL       — mcp-awareness server URL (default: http://localhost:8420)
    GPS_RECEIVER_PORT   — port to listen on (default: 8421)
    GPS_RECEIVER_HOST   — bind address (default: 0.0.0.0)
    GPS_EXPIRES_DAYS    — how long to keep each breadcrumb (default: 90)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime

from starlette.applications import Starlette
from starlette.requests import Request  # noqa: TC002 — used at runtime in signatures
from starlette.responses import JSONResponse
from starlette.routing import Route

from awareness_edge.core.client import AwarenessClient

logger = logging.getLogger(__name__)

AWARENESS_URL = os.environ.get("AWARENESS_URL", "http://localhost:8420")
GPS_RECEIVER_PORT = int(os.environ.get("GPS_RECEIVER_PORT", "8421"))
GPS_RECEIVER_HOST = os.environ.get("GPS_RECEIVER_HOST", "0.0.0.0")
GPS_EXPIRES_DAYS = int(os.environ.get("GPS_EXPIRES_DAYS", "90"))

_client: AwarenessClient | None = None


def _get_client() -> AwarenessClient:
    global _client
    if _client is None:
        _client = AwarenessClient(url=AWARENESS_URL, source="gps")
    return _client


async def handle_location(request: Request) -> JSONResponse:
    """Accept a GPS location update from Tasker."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    lat = body.get("lat")
    lon = body.get("lon")
    if lat is None or lon is None:
        return JSONResponse({"error": "lat and lon are required"}, status_code=400)

    accuracy = body.get("accuracy")
    speed = body.get("speed")
    battery = body.get("battery")
    timestamp = datetime.now(UTC).isoformat()

    parts = [f"lat={lat}, lon={lon}"]
    if accuracy is not None:
        parts.append(f"accuracy={accuracy}m")
    if speed is not None:
        parts.append(f"speed={speed}")
    if battery is not None:
        parts.append(f"battery={battery}%")

    description = f"GPS: {', '.join(parts)} at {timestamp}"

    client = _get_client()
    try:
        result = await client.add_context(
            source="gps",
            tags=["gps", "location"],
            description=description,
            expires_days=GPS_EXPIRES_DAYS,
        )
        logger.info("Stored location: %s (id=%s)", description, result.get("id", "?"))
        return JSONResponse({"status": "ok", "stored": description})
    except Exception:
        logger.exception("Failed to store location")
        return JSONResponse({"error": "failed to store"}, status_code=502)


async def handle_health(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "service": "gps-receiver"})


app = Starlette(
    routes=[
        Route("/location", handle_location, methods=["POST"]),
        Route("/health", handle_health, methods=["GET"]),
    ],
)


def main() -> None:
    """Run the GPS receiver as a standalone HTTP server."""
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info(
        "GPS receiver starting on %s:%d (awareness: %s, retention: %d days)",
        GPS_RECEIVER_HOST,
        GPS_RECEIVER_PORT,
        AWARENESS_URL,
        GPS_EXPIRES_DAYS,
    )
    uvicorn.run(app, host=GPS_RECEIVER_HOST, port=GPS_RECEIVER_PORT, log_level="info")


if __name__ == "__main__":
    main()

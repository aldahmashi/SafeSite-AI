# API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## Health

`GET /health` — Returns service status, version, and environment.

## Videos

| Endpoint | Description |
|---|---|
| `POST /api/videos/upload` | Upload MP4/MOV/AVI for analysis |
| `GET /api/videos` | List all videos |
| `GET /api/videos/{id}` | Get single video |
| `GET /api/videos/{id}/status` | Processing status |
| `GET /api/videos/{id}/incidents` | All incidents for this video |
| `GET /api/videos/{id}/summary` | Full summary with stats |
| `GET /api/videos/{id}/download` | Download annotated video |
| `DELETE /api/videos/{id}` | Delete video and related data |

## Streams

| Endpoint | Description |
|---|---|
| `POST /api/streams/start` | Start RTSP/webcam stream |
| `POST /api/streams/stop/{stream_id}` | Stop stream |
| `GET /api/streams/{stream_id}/status` | Stream status |
| `GET /api/streams/{stream_id}/incidents` | Live incidents |

## Incidents

| Endpoint | Description |
|---|---|
| `GET /api/incidents` | List incidents (filterable) |
| `GET /api/incidents/{id}` | Single incident |
| `GET /api/incidents/high-risk` | HIGH and CRITICAL only |

## Reports

| Endpoint | Description |
|---|---|
| `POST /api/reports/generate/{video_id}` | Generate PDF report |
| `GET /api/reports` | List reports |
| `GET /api/reports/{id}` | Single report |
| `GET /api/reports/{id}/download` | Download PDF |

## Policies

| Endpoint | Description |
|---|---|
| `POST /api/policies/upload` | Upload safety policy PDF |
| `GET /api/policies` | List policy documents |
| `DELETE /api/policies/{id}` | Delete policy document |

## AI Assistant

| Endpoint | Description |
|---|---|
| `POST /api/assistant/chat` | Send message to AI assistant |

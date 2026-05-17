# Universal File Converter

Universal File Converter is a locally deployable, remotely accessible web app for converting documents, images, audio, video, archives, and ebooks. It uses open-source tools (ffmpeg, ImageMagick, LibreOffice, Pandoc, Calibre) when available and falls back to clear error messages when a tool is missing.

## Features

- Drag-and-drop file uploads with batch conversion support
- Searchable, categorized format list with free-text target input
- Conversion queue with progress and job status tracking
- API key support and private-network-only access by default
- CLI mode for local batch conversions
- Extensible converter registry defined in a single place

## Quick Start (Local Python)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in your browser.

### Optional: Install conversion tools

These tools unlock additional formats:

- **ffmpeg** (audio/video)
- **ImageMagick** (images)
- **LibreOffice** (office docs)
- **Pandoc** (documents/markdown)
- **Calibre** `ebook-convert` (ebooks)

If a tool is missing, the API returns a clear error describing the dependency.

## Docker

```bash
docker-compose up --build
```

The app will be available at `http://localhost:8000`.

## API Overview

- `GET /api/formats` — list formats, pipelines, and supported pairs
- `GET /api/conversions?input_ext=pdf` — outputs for a given input
- `POST /api/jobs` — create a conversion job
- `GET /api/jobs/{job_id}` — job status/progress
- `GET /api/jobs/{job_id}/download?file=...` — download output

### Example job request

```bash
curl -X POST http://localhost:8000/api/jobs \
  -F target_format=pdf \
  -F files=@/path/to/document.docx
```

## Configuration

Environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DATA_DIR` | `./data` | Storage location for uploads/results |
| `MAX_UPLOAD_MB` | `200` | Max upload size per file |
| `MAX_WORKERS` | `4` | Parallel conversion workers |
| `API_KEY` | (empty) | If set, require `X-API-Key` header |
| `ALLOW_PUBLIC` | `false` | Allow public (non-private) IP access |
| `ALLOWED_ORIGINS` | localhost origins | CORS origins list |

## CLI Mode

```bash
python backend/cli.py -t pdf -o ./output ./input.docx ./input2.docx
```

## Extending Conversions

1. Update `backend/app/formats.py` to add formats or pipelines.
2. Add or modify converter implementations in `backend/app/converters`.
3. Ensure the pipeline entry maps to a converter tool ID.

`formats.py` is the single source of truth for supported format categories and conversion pipelines.

## Security Notes

- `ALLOW_PUBLIC=false` restricts access to private networks (LAN) and localhost only.
- Set `API_KEY` to require `X-API-Key` on all API requests.
- Bind to `127.0.0.1` if you do not need remote access.

## License

MIT License. See [LICENSE](LICENSE).

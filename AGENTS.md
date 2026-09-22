# Presenter material storage

- Code and versioned scenarios remain in Git. Do not move `.env`, credentials,
  `.venv`, `node_modules`, downloaded models, or technical caches to OneDrive.
- Store new media, captured scenes, scene metadata and render artifacts under
  the directory configured in `materials.local.json`. Python scripts use
  `scripts/material_paths.py`; JavaScript uses `src/material-paths.mjs`.
- Do not recreate repository-local `data`/`output` folders or junctions. All
  working material paths must use `materials.local.json`; fail if it is absent.
- Historical snapshots retain their original paths and are not runtime config.
- Publish canonical OneDrive paths, not compatibility paths, in Google Sheets.
  Detect the video-link column from the current header; do not assume L or M.

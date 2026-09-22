from material_paths import material_dir
"""Inventory an archive without unpacking or modifying any original files."""
import collections
import json
import ntpath
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'sources.local.json').read_text(encoding='utf-8'))
archive = Path(config['camtasiaArchive']['path'])
with zipfile.ZipFile(archive) as bundle:
    entries = bundle.infolist()
    projects = [e for e in entries if e.filename.endswith('.tscproj')]
    report = {
        'archive': str(archive),
        'relationshipToExport': 'unverified',
        'entryCount': len(entries),
        'extensions': dict(collections.Counter(Path(e.filename).suffix for e in entries)),
        'projects': [],
    }
    for entry in projects:
        if entry.file_size > 100 * 1024 * 1024:
            raise ValueError('Project JSON exceeds inspection size limit')
        project = json.loads(bundle.read(entry).decode('utf-8-sig'))
        timeline = project.get('timeline', {})
        edit_rate = project.get('editRate')
        scenes = timeline.get('sceneTrack', {}).get('scenes', [])
        # Inspect top-level clip ends only. Nested groups have local time origins.
        scene_ends = [max((m.get('start', 0) + m.get('duration', 0)
                          for t in scene.get('csml', {}).get('tracks', [])
                          for m in t.get('medias', [])), default=0)
                      for scene in scenes]
        archived_names = {ntpath.basename(e.filename).casefold() for e in entries}
        sources = project.get('sourceBin', [])
        unmatched = [s.get('src') for s in sources if isinstance(s, dict) and s.get('src')
                     and ntpath.basename(s['src']).casefold() not in archived_names]
        report['projects'].append({
            'name': entry.filename,
            'bytes': entry.file_size,
            'topLevelKeys': list(project),
            'timelineKeys': list(timeline) if isinstance(timeline, dict) else [],
            'version': project.get('version'),
            'width': project.get('width'), 'height': project.get('height'),
            'fps': project.get('videoFormatFrameRate'),
            'sceneClipEndSeconds': [end / edit_rate for end in scene_ends] if edit_rate else None,
            'exportDurationSeconds': config.get('inspection', {}).get('videoDurationSeconds'),
            'sourceBinCount': len(sources),
            'sourcesNotMatchedByArchiveBasename': unmatched,
            'sourceMatchCaveat': 'Filename matching is not a checksum or media-decoding integrity check.',
            'timingCaveat': 'Clip extent is not a verified export duration; hidden tracks and export range may differ.',
        })
out = material_dir('output') / 'camtasia-inventory.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True, indent=2))

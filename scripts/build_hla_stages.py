"""Build the first narrated subset of the real HLA1 document, retaining cell IDs."""
from pathlib import Path
import copy
import hashlib
import json
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
source = Path(r'C:\GitHub\coldKode\graph\draw\HLA1.drawio')
out = root / 'diagrams/hla-stages'
out.mkdir(parents=True, exist_ok=True)
raw = source.read_bytes()
doc = ET.fromstring(raw)
cells = {c.get('id'): c for c in doc.findall('.//mxCell')}
result = ET.Element('mxfile', {'host': 'coldKode-presenter'})
page = ET.SubElement(result, 'diagram', {'id': 'hla-stage-001', 'name': '001 — код, граф, диаграмма'})
model = ET.SubElement(page, 'mxGraphModel', {'grid': '0', 'page': '1', 'pageScale': '1', 'pageWidth': '1600', 'pageHeight': '900', 'background': '#FFFFFF'})
nodes = ET.SubElement(model, 'root')
ET.SubElement(nodes, 'mxCell', {'id': '0'})
ET.SubElement(nodes, 'mxCell', {'id': '1', 'parent': '0'})

def derived(cid, x, y, w, h, value=None):
    cell = copy.deepcopy(cells[cid])
    cell.set('parent', '1')
    if value is not None:
        cell.set('value', value)
        cell.set('style', cell.get('style') + ';fontSize=30;fontFamily=Arial;fontColor=#222222;')
    geo = cell.find('mxGeometry')
    geo.attrib.update(x=str(x), y=str(y), width=str(w), height=str(h))
    nodes.append(cell)

def label(cid, text, x, y, w, size=28):
    cell = ET.SubElement(nodes, 'mxCell', {'id': cid, 'value': text, 'parent': '1', 'vertex': '1', 'style': f'text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;fontFamily=Arial;fontSize={size};fontColor=#222222;strokeColor=none;fillColor=none;'})
    ET.SubElement(cell, 'mxGeometry', {'x': str(x), 'y': str(y), 'width': str(w), 'height': '55', 'as': 'geometry'})

def arrow(cid, source_id, target_id):
    cell = ET.SubElement(nodes, 'mxCell', {'id': cid, 'parent': '1', 'edge': '1', 'source': source_id, 'target': target_id, 'style': 'edgeStyle=none;html=1;endArrow=block;endFill=1;strokeWidth=3;strokeColor=#555555;exitX=1;exitY=0.5;entryX=0;entryY=0.5;'})
    ET.SubElement(cell, 'mxGeometry', {'relative': '1', 'as': 'geometry'})

derived('327', 160, 330, 140, 180, 'TS')
derived('228', 690, 327.5, 220, 185, 'Neo4j')
derived('331', 1295, 355, 130, 130)
label('source-caption', 'Исходный код', 85, 540, 290)
label('graph-caption', 'Граф', 655, 540, 290)
label('diagram-caption', 'Диаграмма · draw.io', 1175, 540, 370)
label('extract-caption', 'Извлечение сущностей\nи связей', 330, 290, 330, 23)
label('render-caption', 'Построение диаграммы', 935, 290, 335, 23)
arrow('stage-code-to-graph', '327', '228')
arrow('stage-graph-to-diagram', '228', '331')
ET.indent(result, space='  ')
stage = out / '001-code-graph-diagram.drawio'
stage.write_bytes(ET.tostring(result, encoding='utf-8', xml_declaration=True))
(out / 'HLA1-source.drawio').write_bytes(raw)
(out / '001.manifest.json').write_text(json.dumps({'stage': 1, 'sheetCell': '!C3', 'source': 'HLA1-source.drawio', 'sourceSha256': hashlib.sha256(raw).hexdigest(), 'retainedCellIds': ['327', '228', '331'], 'narration': 'Перед вами будут результаты скриптов, которые извлекают из исходного кода нужные сущности и связи, преобразуют их в граф, а потом создают из графа диграмму.', 'canvas': {'width':1600,'height':900}, 'omittedUntilIntroduced': ['CodeQL','Parquet','DuckDB','importer','coordinator','annotator','agent','MCP','Babel','Redis','runtime'], 'adaptation': 'Source document/database/draw.io symbols retained. React-specific decoration omitted for the generic TypeScript example. Intermediate pipeline collapsed into two forward arrows. All assets in stage embedded; no remote requests.'},ensure_ascii=False,indent=2),encoding='utf-8')
print(stage)

import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const root=fileURLToPath(new URL('../.cache/scene-inspection/',import.meta.url));
// Machine-local, disposable dumps. Scene geometry and validation reports are
// durable material metadata and must NOT use this directory.
export function inspectionCacheDir(sceneDir) {
  const absolute=path.resolve(sceneDir);
  const key=createHash('sha256').update(absolute.replaceAll('\\','/').toLowerCase()).digest('hex').slice(0,16);
  return path.join(root,`${path.basename(absolute)}-${key}`);
}

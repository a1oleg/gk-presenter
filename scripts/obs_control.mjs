// OBS v5 local control. Authentication stays in the local OBS configuration.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';

export async function connectObs() {
  const config = JSON.parse(await fs.readFile(path.join(process.env.APPDATA, 'obs-studio/plugin_config/obs-websocket/config.json'), 'utf8'));
  if (!config.server_enabled) throw new Error('OBS WebSocket disabled');
  const socket = new WebSocket(`ws://127.0.0.1:${config.server_port || 4455}`);
  const pending = new Map();
  const ready = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => { socket.close(); reject(new Error('OBS authentication timed out')); }, 10000);
    socket.addEventListener('error', () => { clearTimeout(timeout); reject(new Error('OBS connection failed')); });
    socket.addEventListener('message', event => {
      const {op,d} = JSON.parse(event.data);
      if (op === 0) {
        const identify = {rpcVersion:1,eventSubscriptions:0};
        if (d.authentication) {
          const hash = text => crypto.createHash('sha256').update(text).digest('base64');
          identify.authentication = hash(hash(config.server_password + d.authentication.salt) + d.authentication.challenge);
        }
        socket.send(JSON.stringify({op:1,d:identify}));
      } else if (op === 2) { clearTimeout(timeout); resolve(); }
      else if (op === 7) {
        const task = pending.get(d.requestId);
        if (task) { pending.delete(d.requestId); clearTimeout(task.timeout); d.requestStatus.result ? task.resolve(d.responseData || {}) : task.reject(new Error(`${d.requestType}: ${d.requestStatus.comment}`)); }
      }
    });
  });
  await ready;
  return {
    request(requestType,requestData={}) {
      return new Promise((resolve,reject) => {
        const requestId = crypto.randomUUID();
        const timeout = setTimeout(() => { pending.delete(requestId); reject(new Error(`OBS request timed out: ${requestType}`)); },15000);
        pending.set(requestId,{resolve,reject,timeout});
        socket.send(JSON.stringify({op:6,d:{requestType,requestId,requestData}}));
      });
    },
    close() { socket.close(); }
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const obs = await connectObs();
  try {
    for (const requestType of ['GetVersion','GetVideoSettings','GetRecordStatus','GetCurrentProgramScene'])
      console.log(JSON.stringify({requestType,...await obs.request(requestType)}));
    const {currentProgramSceneName:sceneName} = await obs.request('GetCurrentProgramScene');
    console.log(JSON.stringify(await obs.request('GetSceneItemList',{sceneName})));
  } finally { obs.close(); }
}

import {renderScene} from '../src/render-service.mjs';
const [sceneDir,...args]=process.argv.slice(2);
if(!sceneDir)throw Error('Usage: node scripts/render_motion_captions.mjs <sceneDir> [--filename name.mp4] [--preview seconds]');
const value=flag=>args.includes(flag)?args[args.indexOf(flag)+1]:undefined;
const controller=new AbortController();process.once('SIGINT',()=>controller.abort());
const preview=value('--preview');let last=0;
console.log(await renderScene({sceneDir,mode:preview===undefined?'video':'preview',time:Number(preview||0),filename:value('--filename'),signal:controller.signal,onProgress:p=>{if(Date.now()-last>3000){console.log(JSON.stringify(p));last=Date.now();}}}));

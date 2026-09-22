import project from './project?project';
import {Renderer,Vector2} from '@motion-canvas/core';
(window as any).renderCaptions=async(scene:any)=>{
 (window as any).presenterScene=scene;
 const renderer=new Renderer(project);
 const errors:any[]=[];project.logger.onLogged.subscribe((entry:any)=>{if(entry.level==='error')errors.push({message:entry.message,stack:entry.stack,object:String(entry.object)});});
 await renderer.render({name:'captions',range:[0,scene.duration],fps:30,size:new Vector2(1920,1080),resolutionScale:1,colorSpace:'srgb',background:null,exporter:{name:'coldkode-frames',options:{}}});
 if(errors.length)throw Error(JSON.stringify(errors));
 return {renderer:'Motion Canvas 3.17.2',duration:scene.duration};
};

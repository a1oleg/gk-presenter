import {makeProject,ObjectMetaField} from '@motion-canvas/core';
import captions from './scenes/captions?scene';
class PresenterExporter {
 static id='graphKoda-frames'; static displayName='graphKoda FFmpeg stream';
 static meta(){return new ObjectMetaField('Options',{});}
 static async create(){return new PresenterExporter();}
 async handleFrame(canvas:HTMLCanvasElement,frame:number){await (window as any).emitFrame(frame,canvas.toDataURL('image/png'));}
}
export default makeProject({scenes:[captions],plugins:[{name:'graphKoda-export',exporters:()=>[PresenterExporter]}]});

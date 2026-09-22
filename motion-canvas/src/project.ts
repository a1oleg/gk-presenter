import {makeProject,ObjectMetaField} from '@motion-canvas/core';
import captions from './scenes/captions?scene';
class PresenterExporter {
 static id='coldkode-frames'; static displayName='coldKode transparent frames';
 static meta(){return new ObjectMetaField('Options',{});}
 static async create(){return new PresenterExporter();}
 async handleFrame(canvas:HTMLCanvasElement,frame:number){await (window as any).saveFrame(frame,canvas.toDataURL('image/png'));}
}
export default makeProject({scenes:[captions],plugins:[{name:'coldkode-export',exporters:()=>[PresenterExporter]}]});

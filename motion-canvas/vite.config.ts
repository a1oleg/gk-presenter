import {defineConfig} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';
const plugin=typeof motionCanvas==='function'?motionCanvas:(motionCanvas as any).default;
export default defineConfig({plugins:[plugin()],server:{host:'127.0.0.1',port:9031,strictPort:true}});

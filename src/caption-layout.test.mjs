import test from 'node:test';import assert from 'node:assert/strict';
import {captionLayout} from './caption-layout.mjs';
// Two actually observed positions from the row-11 recording session.
const observed={anchor:{x:49.5,y:123.44,width:64.38,height:33.3},canvas:{width:1920,height:1080},code:{targetLine:25,lineHeight:28,viewportTop:48}};
test('row 11 rejects its earlier code position',()=>{
 const r=captionLayout({...observed,code:{...observed.code,visibleStartLine:18}});
 assert.equal(r.safe,false);assert.equal(r.requiredDownwardPixels,30);
});
test('row 11 accepts the recorded position below the floating captions',()=>{
 const r=captionLayout({...observed,code:{...observed.code,visibleStartLine:16}});
 assert.equal(r.safe,true);assert.deepEqual(r.rect,{x:214,y:116,width:1480,height:96});assert.equal(r.codeTopLowerBound,272);
});

// Coordinates here are output-video pixels, not diagram model coordinates.
export function captionLayout({anchor,canvas,code}){
 const rect={x:Math.ceil(anchor.x+anchor.width+100),y:Math.ceil(anchor.y-8),width:1480,height:96};
 rect.width=Math.min(rect.width,canvas.width-rect.x-24);
 if(rect.width<1460)throw Error('Caption panel cannot fit at this anchor; select a different layout');
 const shadow=10,minimumGap=24,requiredCodeY=rect.y+rect.height+shadow+minimumGap;
 // VS Code may report a partly visible first line: discard one entire line.
 const codeTopLowerBound=code.viewportTop+(code.targetLine-code.visibleStartLine-1)*code.lineHeight;
 return {rect,exclusion:{...rect,height:rect.height+shadow},requiredCodeY,codeTopLowerBound,safe:codeTopLowerBound>=requiredCodeY,requiredDownwardPixels:Math.max(0,requiredCodeY-codeTopLowerBound),calibration:code};
}

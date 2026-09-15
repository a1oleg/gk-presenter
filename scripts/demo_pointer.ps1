param([ValidateSet('inspect','scroll','drag','move')][string]$Action='inspect',[int]$X=0,[int]$Y=0,[int]$TargetX=0,[int]$TargetY=0,[int]$Ticks=5)
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public class DemoPointer {
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 public delegate bool EnumProc(IntPtr h,IntPtr p);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p,IntPtr l);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h,StringBuilder t,int n);
 public static IntPtr[] FindFisher(){var found=new List<IntPtr>();EnumWindows((h,p)=>{var t=new StringBuilder(1024);GetWindowText(h,t,1024);if(t.ToString().Contains("coldKode (Workspace) - Visual Studio Code"))found.Add(h);return true;},IntPtr.Zero);return found.ToArray();}
 [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h,int a,out RECT r,int s);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,int data,UIntPtr extra);
}
'@
[void][DemoPointer]::SetProcessDPIAware()
$windows=@([DemoPointer]::FindFisher())
if($windows.Count -ne 1){throw 'Expected one Fisher-Yates VS Code window'}
$window=$windows[0];$rect=New-Object DemoPointer+RECT
[void][DemoPointer]::DwmGetWindowAttribute($window,9,[ref]$rect,16)
if($Action -eq 'inspect'){ $rect | ConvertTo-Json;exit }
if($X -lt 0 -or $Y -lt 0 -or $X -ge ($rect.Right-$rect.Left) -or $Y -ge ($rect.Bottom-$rect.Top)){throw 'Point outside Fisher window'}
[void][DemoPointer]::SetForegroundWindow($window)
[void][DemoPointer]::SetCursorPos($rect.Left+$X,$rect.Top+$Y)
Start-Sleep -Milliseconds 100
if($Action -eq 'scroll'){
 for($i=0;$i -lt $Ticks;$i++){[DemoPointer]::mouse_event(0x0800,0,0,-120,[UIntPtr]::Zero);Start-Sleep -Milliseconds 180}
}
if($Action -eq 'drag'){
 if($TargetX -lt 0 -or $TargetX -ge ($rect.Right-$rect.Left) -or $TargetY -lt 0 -or $TargetY -ge ($rect.Bottom-$rect.Top)){throw 'Drag target outside Fisher window'}
 [DemoPointer]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero)
 try{for($i=1;$i -le 45;$i++){[void][DemoPointer]::SetCursorPos($rect.Left+[int]($X+($TargetX-$X)*$i/45),$rect.Top+[int]($Y+($TargetY-$Y)*$i/45));Start-Sleep -Milliseconds 20}}
 finally{[DemoPointer]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)}
}

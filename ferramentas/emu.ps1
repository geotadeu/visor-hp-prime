param([string]$cmd, [string]$arg, [int]$x=0, [int]$y=0)
# Helper to drive the HP Prime emulator window: shot | keys | click | front
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
 [DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int hh,bool r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, int f);
 [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, int f, int e);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindow(string c, string t);
 public delegate bool EP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EP f, IntPtr l);
 [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 public static IntPtr Biggest(int pid) { IntPtr best=IntPtr.Zero; int area=0;
   EnumWindows((h,l)=>{ int p; GetWindowThreadProcessId(h,out p); if(p==pid && IsWindowVisible(h)){ RECT r; GetWindowRect(h,out r); int a=(r.R-r.L)*(r.B-r.T); if(a>area){area=a;best=h;} } return true; }, IntPtr.Zero); return best; }
 public struct RECT { public int L, T, R, B; }
}
"@
[W]::SetProcessDPIAware() | Out-Null
$p = Get-Process HPPrime -ErrorAction SilentlyContinue | ? MainWindowHandle -ne 0 | Select -First 1
if (-not $p) { "no emulator window"; exit 1 }
$h = [W]::Biggest($p.Id)
if ($h -eq [IntPtr]::Zero) { "no window"; exit 1 }
[W]::ShowWindow($h, 9) | Out-Null
$r0 = New-Object W+RECT; [W]::GetWindowRect($h, [ref]$r0) | Out-Null
if ($r0.L -lt 0 -or $r0.T -lt 0) { [W]::MoveWindow($h, 60, 60, $r0.R-$r0.L, $r0.B-$r0.T, $true) | Out-Null }
[W]::keybd_event(0x12,0,0,0); [W]::keybd_event(0x12,0,2,0)
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 300
Add-Type @"
using System; using System.Runtime.InteropServices; public class W3 { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); }
"@
if ([W3]::GetForegroundWindow() -ne $h -and $cmd -ne 'shot') { "emulator not in foreground, aborting"; exit 1 }
$r = New-Object W+RECT; [W]::GetWindowRect($h, [ref]$r) | Out-Null
switch ($cmd) {
 'shot' {
   $w = $r.R - $r.L; $hh = $r.B - $r.T
   $bmp = New-Object Drawing.Bitmap $w, $hh
   $g = [Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
   $bmp.Save($arg, [Drawing.Imaging.ImageFormat]::Png); "rect $($r.L),$($r.T) ${w}x$hh"
 }
 'keys' { [Windows.Forms.SendKeys]::SendWait($arg); Start-Sleep -Milliseconds 400; "sent" }
 'click' {
   [W]::SetCursorPos($r.L + $x, $r.T + $y); Start-Sleep -Milliseconds 100
   [W]::mouse_event(2,0,0,0,0); Start-Sleep -Milliseconds 80; [W]::mouse_event(4,0,0,0,0)
   Start-Sleep -Milliseconds 400; "clicked"
 }
 'drag' {
   $x2 = [int]$arg.Split(',')[0]; $y2 = [int]$arg.Split(',')[1]
   [W]::SetCursorPos($r.L + $x, $r.T + $y); [W]::mouse_event(2,0,0,0,0)
   for ($i=1; $i -le 10; $i++) { [W]::SetCursorPos($r.L + $x + ($x2-$x)*$i/10, $r.T + $y + ($y2-$y)*$i/10); Start-Sleep -Milliseconds 40 }
   [W]::mouse_event(4,0,0,0,0); Start-Sleep -Milliseconds 400; "dragged"
 }
 'front' { "rect $($r.L),$($r.T),$($r.R),$($r.B)" }
}

param([string]$keys, [string]$prefix)
# Press a sequence of named calculator keys, capturing the screen after each; montage to $prefix.png
# names: plus minus up down left right three nine esc enter
$S = $PSScriptRoot
$pos = @{ plus=@(309,755); minus=@(309,712); up=@(176,363); down=@(176,442); left=@(137,402); right=@(213,402);
          three=@(243,712); nine=@(243,620); esc=@(307,380); enter=@(280,575) }
Add-Type -AssemblyName System.Drawing
$shots = @()
& "$S\emu.ps1" shot "$S\${prefix}_0.png" | Out-Null; $shots += "$S\${prefix}_0.png"
$i = 0
foreach ($k in $keys.Split(',')) {
  $i++
  & "$S\emu.ps1" click '' $pos[$k][0] $pos[$k][1] | Out-Null
  Start-Sleep 2
  & "$S\emu.ps1" shot "$S\${prefix}_$i.png" | Out-Null; $shots += "$S\${prefix}_$i.png"
}
$cols = 4; $rows = [math]::Ceiling($shots.Count / $cols)
$b = New-Object Drawing.Bitmap (330*$cols), (245*$rows); $g = [Drawing.Graphics]::FromImage($b)
for ($k = 0; $k -lt $shots.Count; $k++) {
  $im = [Drawing.Image]::FromFile($shots[$k])
  $g.DrawImage($im, (New-Object Drawing.Rectangle (($k % $cols)*330), ([math]::Floor($k/$cols)*245), 325, 240), (New-Object Drawing.Rectangle 10, 100, 325, 240), 'Pixel')
  $im.Dispose()
}
$b.Save("$S\$prefix.png")

param([string]$src, [string]$out, [switch]$noclear)
# In the emulator's program editor: clear all, paste $src, press Verif, screenshot to $out
$S = $PSScriptRoot
if (-not $noclear) {
  & "$S\emu.ps1" click '' 33 710 | Out-Null      # Shift
  & "$S\emu.ps1" click '' 307 380 | Out-Null     # Esc -> Clear
  Start-Sleep -Milliseconds 500
  & "$S\emu.ps1" click '' 302 330 | Out-Null     # OK
}
Get-Content -Raw -Encoding UTF8 $src | Set-Clipboard
& "$S\emu.ps1" click '' 170 200 | Out-Null
& "$S\emu.ps1" keys '^v' | Out-Null
Start-Sleep 1
& "$S\emu.ps1" click '' 302 330 | Out-Null       # Verif
Start-Sleep 2
& "$S\emu.ps1" shot $out

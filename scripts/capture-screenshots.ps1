# Capture real VS Code screenshots for Luminous Morna Theme.
#
# Launches a throwaway VS Code profile (temp --user-data-dir / --extensions-dir)
# with the extension installed, opens the demo workspace, maximises the window and
# grabs it with GDI. Raw PNGs land in an ASCII temp folder; run
# scripts/finalize_screenshots.py afterwards to place them in store-assets/.
#
# Usage (from anywhere):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\capture-screenshots.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\capture-screenshots.ps1 -Variant dark
#
# Keep this file pure ASCII: it is parsed as ANSI by Windows PowerShell 5.1.

param(
    [string]$Variant = "dark,light",
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class MornaWin {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hWnd, int attr, out RECT val, int size);
}
"@

[MornaWin]::SetProcessDPIAware() | Out-Null

$root = Split-Path -Parent $PSScriptRoot
$themeLabels = @{ dark = "Luminous Morna Theme Dark"; light = "Luminous Morna Theme Light" }

$settingsTemplate = @'
{
  "workbench.colorTheme": "__THEME__",
  "workbench.startupEditor": "none",
  "workbench.tips.enabled": false,
  "workbench.editor.tabSizing": "shrink",
  "workbench.enableExperiments": false,
  "workbench.editor.enablePreview": false,
  "workbench.secondarySideBar.defaultVisibility": "hidden",
  "chat.commandCenter.enabled": false,
  "chat.disableAIFeatures": true,
  "typescript.validate.enable": false,
  "javascript.validate.enable": false,
  "window.commandCenter": false,
  "window.zoomLevel": 0,
  "security.workspace.trust.enabled": false,
  "telemetry.telemetryLevel": "off",
  "update.mode": "none",
  "update.showReleaseNotes": false,
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,
  "editor.fontFamily": "Cascadia Code, Consolas, monospace",
  "editor.fontSize": 14,
  "editor.lineHeight": 1.6,
  "editor.minimap.enabled": true,
  "editor.cursorBlinking": "solid",
  "editor.renderWhitespace": "none",
  "editor.guides.indentation": true,
  "breadcrumbs.enabled": true,
  "explorer.compactFolders": false,
  "git.enabled": false,
  "git.decorations.enabled": false
}
'@

foreach ($name in ($Variant -split ",")) {
    $name = $name.Trim()
    if ($name -ne "dark" -and $name -ne "light") { throw "unknown variant '$name'" }
    $tmp = Join-Path $env:TEMP ("morna-shot-" + $name)
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }

    $dataDir = Join-Path $tmp "data"
    $extDir  = Join-Path $tmp "ext"
    $wsDir   = Join-Path $tmp "morna-demo"
    $userDir = Join-Path $dataDir "User"
    New-Item -ItemType Directory -Force -Path $userDir, $extDir, $wsDir | Out-Null

    # install the extension into the throwaway profile
    $extTarget = Join-Path $extDir "luminous-morna-theme"
    New-Item -ItemType Directory -Force -Path $extTarget | Out-Null
    Copy-Item (Join-Path $root "package.json") $extTarget -Force
    Copy-Item (Join-Path $root "themes") $extTarget -Recurse -Force
    Copy-Item (Join-Path $root "store-assets\demo\*") $wsDir -Recurse -Force

    $settings = $settingsTemplate.Replace("__THEME__", $themeLabels[$name])
    Set-Content -Path (Join-Path $userDir "settings.json") -Value $settings -Encoding UTF8

    $entry = Join-Path $wsDir "app.ts"
    Write-Host "launching VS Code for variant '$name' ..."
    $launched = Get-Date
    Start-Process -FilePath "code.cmd" -ArgumentList @(
        "--user-data-dir=$dataDir",
        "--extensions-dir=$extDir",
        "--new-window",
        "--skip-welcome",
        "--disable-workspace-trust",
        "--disable-telemetry",
        "--goto", ($entry + ":34"),
        $wsDir
    ) -WindowStyle Hidden | Out-Null

    # wait for the workbench window
    $proc = $null
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 1500
        $candidate = Get-Process -Name Code -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*morna-demo*" } |
            Select-Object -First 1
        if ($candidate) { $proc = $candidate; break }
    }
    if (-not $proc) { throw "VS Code window for '$name' did not appear within $TimeoutSeconds s" }

    Write-Host ("window found: " + $proc.MainWindowTitle)
    Start-Sleep -Seconds 6   # let fonts, tokens and the extension host settle

    # Raise the window. A background process is not allowed to steal the
    # foreground, so nudge it with a bare ALT press first (the documented
    # workaround); if that still fails we fall back to PrintWindow, which
    # reads the window's own DC and works even when it stays covered.
    $hwnd = $proc.MainWindowHandle
    [MornaWin]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)   # ALT down
    [MornaWin]::ShowWindow($hwnd, 3) | Out-Null            # SW_MAXIMIZE
    [MornaWin]::SetForegroundWindow($hwnd) | Out-Null
    [MornaWin]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)   # ALT up
    Start-Sleep -Seconds 5
    [MornaWin]::ShowWindow($hwnd, 3) | Out-Null
    Start-Sleep -Seconds 3

    $rect = New-Object MornaWin+RECT
    [MornaWin]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
    $w = $rect.Right - $rect.Left
    $h = $rect.Bottom - $rect.Top
    if ($w -lt 800 -or $h -lt 600) { throw "captured window too small: ${w}x${h}" }

    $foreground = ([MornaWin]::GetForegroundWindow() -eq $hwnd)
    Write-Host ("window in front: " + $foreground)

    # PrintWindow reads the window's own DC, so desktop popups that happen to
    # float above it (chat clients, toasts) never end up in the shot.
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $gfx = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $gfx.GetHdc()
    [MornaWin]::PrintWindow($hwnd, $hdc, 2) | Out-Null       # PW_RENDERFULLCONTENT
    $gfx.ReleaseHdc($hdc)
    $gfx.Dispose()

    # GetWindowRect includes the invisible resize frame, which is rendered as a
    # dark line - very visible on a light theme. DWMWA_EXTENDED_FRAME_BOUNDS
    # gives the visible frame; trim 3 more physical px for the 1px OS border.
    $dwm = New-Object MornaWin+RECT
    $hr = [MornaWin]::DwmGetWindowAttribute($hwnd, 9, [ref]$dwm, 16)
    $cropL = $dwm.Left - $rect.Left + 3
    $cropT = $dwm.Top - $rect.Top + 3
    $cropR = $w - ($rect.Right - $dwm.Right) - 3
    $cropB = $h - ($rect.Bottom - $dwm.Bottom) - 3
    Write-Host ("dwm hr=$hr rect=$($dwm.Left),$($dwm.Top),$($dwm.Right),$($dwm.Bottom) crop=$cropL,$cropT,$cropR,$cropB")

    $shot = $bmp
    if ($hr -eq 0 -and $cropR -gt $cropL -and $cropB -gt $cropT -and
        $cropL -ge 0 -and $cropT -ge 0 -and $cropR -le $w -and $cropB -le $h) {
        $box = New-Object System.Drawing.Rectangle($cropL, $cropT, ($cropR - $cropL), ($cropB - $cropT))
        $shot = $bmp.Clone($box, $bmp.PixelFormat)
    } else {
        Write-Host "frame bounds unusable - keeping the full window rect"
    }

    $raw = Join-Path $tmp "raw-$name.png"
    $shot.Save($raw, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Host ("saved $raw ($($shot.Width)x$($shot.Height)) [PrintWindow]")
    if (-not [object]::ReferenceEquals($shot, $bmp)) { $shot.Dispose() }
    $bmp.Dispose()

    # backup: plain screen grab (includes anything floating on top)
    $bmp2 = New-Object System.Drawing.Bitmap($w, $h)
    $gfx2 = [System.Drawing.Graphics]::FromImage($bmp2)
    $gfx2.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size($w, $h)))
    $grab = Join-Path $tmp "grab-$name.png"
    $bmp2.Save($grab, [System.Drawing.Imaging.ImageFormat]::Png)
    $gfx2.Dispose(); $bmp2.Dispose()
    Write-Host "saved $grab [screen grab]"

    $proc.CloseMainWindow() | Out-Null
    Start-Sleep -Seconds 3
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
    Start-Sleep -Seconds 2
}

Write-Host "done"

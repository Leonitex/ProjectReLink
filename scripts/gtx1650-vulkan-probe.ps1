# Read-only diagnostic for Project ReLink on NVIDIA GTX 1650.
# Checks nvidia-smi and vulkaninfo without modifying drivers or game files.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\gtx1650-vulkan-probe.ps1
$ErrorActionPreference = 'Stop'
Write-Output '=== NVIDIA GPU and VRAM (MiB) ==='
$nv = Get-Command 'nvidia-smi.exe' -ErrorAction SilentlyContinue
$nvPath = if ($nv) { $nv.Source } else { $null }
if (-not $nvPath) {
    $candidate = Join-Path $env:ProgramFiles 'NVIDIA Corporation\NVSMI\nvidia-smi.exe'
    if (Test-Path -LiteralPath $candidate) { $nvPath = $candidate }
}
if ($nvPath) {
    try {
        & $nvPath '--query-gpu=name,driver_version,memory.total,memory.used,memory.free' '--format=csv,noheader,nounits'
    } catch {
        Write-Output "nvidia-smi query unavailable: $($_.Exception.Message)"
    }
} else {
    Write-Output 'nvidia-smi not found. See Task Manager > Performance > GPU > Dedicated GPU memory.'
}
Write-Output ''
Write-Output '=== Vulkan capability check ==='
$vulkan = Get-Command 'vulkaninfo.exe' -ErrorAction SilentlyContinue
if (-not $vulkan) {
    Write-Output 'vulkaninfo is not installed or is not in PATH; this optional Vulkan SDK tool is not required to play.'
    Write-Output 'ReLink also reports the chosen GPU in its startup log.'
    exit 0
}

# Windows PowerShell 5.1 with ErrorActionPreference Stop may treat stderr output from native
# tools as a terminating error. A missing third-party overlay JSON can be non-fatal.
# Capture stdout/stderr separately, then inspect the actual exit code.
function Invoke-VulkanInfo([string[]] $Arguments) {
    $key = [guid]::NewGuid().ToString('N')
    $out = Join-Path $env:TEMP ("relink-vulkan-$key-out.txt")
    $err = Join-Path $env:TEMP ("relink-vulkan-$key-err.txt")
    try {
        if ($Arguments.Count -gt 0) {
            $p = Start-Process -FilePath $vulkan.Source -ArgumentList $Arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
        } else {
            $p = Start-Process -FilePath $vulkan.Source -NoNewWindow -Wait -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
        }
        return [pscustomobject]@{
            ExitCode = $p.ExitCode
            StdOut = [System.IO.File]::ReadAllText($out)
            StdErr = [System.IO.File]::ReadAllText($err)
        }
    } finally {
        Remove-Item -LiteralPath $out, $err -Force -ErrorAction SilentlyContinue
    }
}

try {
    $summary = Invoke-VulkanInfo @('--summary')
    if ($summary.StdErr -match 'EOSOverlayVkLayer.*json') {
        Write-Output 'Note: Epic overlay JSON warning detected; this may not block Vulkan.'
    }
    if ($summary.ExitCode -ne 0) {
        Write-Output "vulkaninfo --summary failed (exit $($summary.ExitCode)):"
        Write-Output (($summary.StdErr -split '\r?\n' | Where-Object { $_ }) | Select-Object -First 4)
        exit 1
    }
    Write-Output 'Summary:'
    $summary.StdOut -split '\r?\n' |
        Where-Object { $_ -match 'deviceName\s*=|apiVersion\s*=|driverName\s*=|driverInfo\s*=' } |
        Select-Object -First 25 | ForEach-Object { Write-Output $_.Trim() }

    $detail = Invoke-VulkanInfo @()
    if ($detail.ExitCode -ne 0) {
        Write-Output "Full vulkaninfo failed (exit $($detail.ExitCode)); mesh shader support not established."
        Write-Output (($detail.StdErr -split '\r?\n' | Where-Object { $_ }) | Select-Object -First 4)
        exit 1
    }
    $hasExt = [bool]($detail.StdOut -match '(?m)^\s*VK_EXT_mesh_shader\s*:')
    $hasMesh = [bool]($detail.StdOut -match '(?m)^\s*meshShader\s*=\s*(true|VK_TRUE|1)\s*$')
    Write-Output "VK_EXT_mesh_shader extension listed: $hasExt"
    Write-Output "meshShader feature reported true: $hasMesh"
    Write-Output 'If several GPUs are shown, these flags may belong to different GPUs; check the ReLink device log.'
    if ($detail.StdErr -match 'EOSOverlayVkLayer.*json') {
        Write-Output 'Note: the Epic overlay warning also occurred in the full report.'
    }
} catch {
    Write-Output "Vulkan query could not complete: $($_.Exception.Message)"
    exit 1
}

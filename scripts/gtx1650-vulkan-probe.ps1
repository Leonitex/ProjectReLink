# Read-only NVIDIA/Vulkan capability check for a low-VRAM Project ReLink baseline.
# Does not install anything, edit drivers, launch games, or include personal account details.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\gtx1650-vulkan-probe.ps1

$ErrorActionPreference = "Stop"
Write-Output "=== NVIDIA GPU and VRAM (MiB) ==="
$nv = Get-Command "nvidia-smi.exe" -ErrorAction SilentlyContinue
$nvPath = if ($nv) { $nv.Source } else { $null }
if (-not $nvPath) {
    $candidate = Join-Path $env:ProgramFiles "NVIDIA Corporation\NVSMI\nvidia-smi.exe"
    if (Test-Path -LiteralPath $candidate) { $nvPath = $candidate }
}
if ($nvPath) {
    try {
        & $nvPath "--query-gpu=name,driver_version,memory.total,memory.used,memory.free" "--format=csv,noheader,nounits"
    } catch {
        Write-Output "nvidia-smi could not query the driver: $($_.Exception.Message)"
    }
} else {
    Write-Output "nvidia-smi was not found. Alternative: Task Manager > Performance > GPU > Dedicated GPU memory."
}
Write-Output ""
Write-Output "=== Vulkan tool check ==="
$vulkan = Get-Command "vulkaninfo.exe" -ErrorAction SilentlyContinue
if (-not $vulkan) {
    Write-Output "vulkaninfo is not installed or not in PATH. This is not a failure: it is an optional Vulkan SDK utility."
    Write-Output "ReLink's startup log also reports Vulkan GPU selection and feature support."
    exit 0
}
try {
    $summary = (& $vulkan.Source "--summary" 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "vulkaninfo --summary exited with code $LASTEXITCODE" }
    $interesting = $summary -split "[\r\n]+" | Where-Object {
        $_ -match "deviceName\s*=|apiVersion\s*=|driverName\s*=|driverInfo\s*="
    }
    $interesting | ForEach-Object { Write-Output $_.Trim() }
    Write-Output ""
    Write-Output "=== VK_EXT_mesh_shader probe ==="
    $verbose = (& $vulkan.Source 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "vulkaninfo exited with code $LASTEXITCODE" }
    $extension = $verbose -match "(?m)^\s*VK_EXT_mesh_shader\s*:"
    $feature = $verbose -match "(?m)^\s*meshShader\s*=\s*(true|VK_TRUE|1)\s*$"
    Write-Output "Extension listed by vulkaninfo: $extension"
    Write-Output "meshShader feature reported true: $feature"
    Write-Output "If multiple GPUs are present, this combined output is not per-GPU evidence."
    Write-Output "Check the ReLink Vulkan log for which GPU it actually uses."
} catch {
    Write-Output "Vulkan probe unavailable: $($_.Exception.Message)"
}

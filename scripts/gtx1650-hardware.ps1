# Read-only hardware inventory for Project ReLink's low-VRAM performance work.
# Does not read game files, saves, browser data, serial numbers, or account details.
param([string]$OutFile = "")
$ErrorActionPreference = 'Stop'

try {
    $cpu = @(Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors)
    $gpu = @(Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, VideoProcessor)
    $system = Get-CimInstance Win32_ComputerSystem
    $os = Get-CimInstance Win32_OperatingSystem
} catch {
    Write-Error "Unable to read local hardware details: $($_.Exception.Message)"
    exit 1
}

$report = [ordered]@{
    collected_utc = (Get-Date).ToUniversalTime().ToString('o')
    operating_system = [ordered]@{ name = $os.Caption; version = $os.Version; build = $os.BuildNumber }
    memory_gb = [math]::Round(([double]$system.TotalPhysicalMemory / 1GB), 2)
    cpu = $cpu
    gpu = $gpu
    note = 'GPU dedicated VRAM, Vulkan 1.3 and mesh-shader support require confirmation from the graphics driver / Vulkan diagnostics. Win32_VideoController.AdapterRAM is deliberately not used because it can be unreliable on 4+ GB GPUs.'
}
$json = $report | ConvertTo-Json -Depth 6
if ($OutFile) {
    $target = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutFile)
    $parent = Split-Path -Parent $target
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Set-Content -LiteralPath $target -Value $json -Encoding UTF8
    Write-Output "Hardware report saved: $target"
} else {
    Write-Output $json
}

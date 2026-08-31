# Registers a Windows Scheduled Task that runs the pipeline once a day at 09:00,
# so real daily history accumulates for the evaluation step even when this
# machine isn't actively being worked on. Safe to re-run (overwrites the
# existing task definition via -Force).
#
# To remove: Unregister-ScheduledTask -TaskName "BrandRiskRadarDailyIngest" -Confirm:$false

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptDir "run_daily.bat"

$action = New-ScheduledTaskAction -Execute $batPath
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName "BrandRiskRadarDailyIngest" `
    -Action $action -Trigger $trigger -Settings $settings -Force

Write-Host "Registered. It will run daily at 09:00 (or on next login/wake if the PC was off)."
Write-Host "Logs land in logs\daily_run.log. Check status with:"
Write-Host "  Get-ScheduledTask -TaskName BrandRiskRadarDailyIngest | Get-ScheduledTaskInfo"

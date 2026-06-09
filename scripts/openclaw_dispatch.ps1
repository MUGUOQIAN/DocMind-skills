# OpenClaw /docmind 斜杠命令（Windows PowerShell）
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dispatch = Join-Path $ScriptDir "openclaw_dispatch.py"
$AllArgs = $Args -join " "
if (-not $AllArgs) {
    Write-Error "用法: openclaw_dispatch.ps1 preview --desktop"
    exit 2
}
& python $Dispatch @Args
exit $LASTEXITCODE

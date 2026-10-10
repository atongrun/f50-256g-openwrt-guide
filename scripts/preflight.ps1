param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9._:-]+$')][string]$Serial,
    [string]$Adb='adb',
    [Parameter(Mandatory=$true)][string]$OutputFile
)
$ErrorActionPreference='Stop'
# Read-only. It never enables debugging, obtains root, reboots or writes a device file.
$devices=& $Adb devices
if($LASTEXITCODE -ne 0){throw 'ADB failed'}
if(-not ($devices | Where-Object { $_ -match ('^'+[regex]::Escape($Serial)+'\s+device$') })){
    throw 'The explicitly selected device is not authorized/online.'
}
function Read-Adb([string]$Command){
    $text=& $Adb -s $Serial shell $Command 2>&1
    $exit=$LASTEXITCODE
    return @{exit_code=$exit; output=($text -join "`n").Trim()}
}
$checks=[ordered]@{}
$checks.model=Read-Adb 'getprop ro.product.model'
$checks.board=Read-Adb 'getprop ro.product.board'
$checks.firmware=Read-Adb 'getprop ro.build.display.id'
$checks.slot=Read-Adb 'getprop ro.boot.slot_suffix'
$checks.kernel=Read-Adb 'uname -r'
$checks.shell=Read-Adb 'id'
$checks.root=Read-Adb 'su -c id'
$checks.block_inventory=Read-Adb 'cat /proc/partitions'
$checks.bootmode=Read-Adb 'getprop ro.bootmode'
$checks.notice='This is not a GPT or backup verification. No write is authorized by this report. Serial and identity properties were deliberately not collected.'
$result=$checks | ConvertTo-Json -Depth 5
$target=[IO.Path]::GetFullPath($OutputFile)
if(Test-Path -LiteralPath $target){throw 'Refusing to overwrite an existing report.'}
[IO.File]::WriteAllText($target,$result,(New-Object Text.UTF8Encoding($false)))
if([IO.File]::ReadAllText($target) -ne $result){throw 'Report readback failed'}
Write-Output "Read-only preflight saved. Review model, slot, root and capacity before continuing: $target"

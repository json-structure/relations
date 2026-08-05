<#
.SYNOPSIS
    Validates the JSON Structure: Relations samples.

.DESCRIPTION
    Runs four checks:

      1. The extension meta-schema (relations-v0.json) is a conforming JSON
         Structure schema document. Skipped unless the json-structure/meta
         repository is checked out beside this one, because the meta-schema
         imports the Extended meta-schema.
      2. Every sample schema conforms to JSON Structure Core and the extensions
         it declares in $uses.
      3. Every example.json instance conforms to the schema beside it.
      4. Every relation in every sample resolves: names do not collide with
         properties, targets carry an identity, scopes hold the target type,
         and every identity in an instance finds exactly one object in scope.

    Steps 1 to 3 use the JSON Structure Python SDK. Install it with
    'pip install json-structure'. Step 4 uses check-relations.py, which
    implements the cross-node and instance-level rules the SDK validators do
    not reach.

.EXAMPLE
    ./validate-samples.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$toolsRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent $toolsRoot
$workspaceRoot = Split-Path -Parent $repoRoot
# The worked examples live in the json-structure/primer-and-samples repository,
# checked out beside this one.
$samplesRoot = Join-Path $workspaceRoot 'primer-and-samples/samples/relations'
$metaSchema = Join-Path $repoRoot 'relations-v0.json'
$extendedMeta = Join-Path $workspaceRoot 'meta/extended/v0/index.json'
$coreMeta = Join-Path $workspaceRoot 'meta/core/v0/index.json'

$failures = 0

function Write-Result {
    param([bool]$Ok, [string]$Label, [string[]]$Detail)

    if ($Ok) {
        Write-Host "  [ok]   $Label" -ForegroundColor Green
    }
    else {
        Write-Host "  [fail] $Label" -ForegroundColor Red
        foreach ($line in $Detail) { Write-Host "         $line" -ForegroundColor Red }
        $script:failures++
    }
}

Write-Host 'Extension meta-schema' -ForegroundColor Cyan
if ((Test-Path $extendedMeta) -and (Test-Path $coreMeta)) {
    $output = & json-structure-check --metaschema --extended --allowimport `
        -m "https://json-structure.org/meta/extended/v0/#=$extendedMeta" `
        -m "https://json-structure.org/meta/core/v0/#=$coreMeta" `
        --quiet $metaSchema 2>&1
    Write-Result ($LASTEXITCODE -eq 0) 'relations-v0.json' $output
}
else {
    Write-Host '  [skip] relations-v0.json (json-structure/meta not checked out beside this repository)' -ForegroundColor Yellow
}

if (-not (Test-Path $samplesRoot)) {
    Write-Host "Samples not found at $samplesRoot" -ForegroundColor Red
    Write-Host 'Check out json-structure/primer-and-samples beside this repository.' -ForegroundColor Red
    exit 1
}

$samplesRootFull = (Resolve-Path $samplesRoot).Path
$schemas = Get-ChildItem -Path $samplesRoot -Recurse -Filter 'schema.struct.json' | Sort-Object FullName

function Get-Label {
    param($Schema)
    $path = $Schema.Directory.FullName
    if ($path.StartsWith($samplesRootFull)) {
        $path = $path.Substring($samplesRootFull.Length).TrimStart('\', '/')
    }
    return $path -replace '\\', '/'
}

Write-Host 'Sample schemas' -ForegroundColor Cyan
foreach ($schema in $schemas) {
    $output = & json-structure-check --extended --allowimport --quiet $schema.FullName 2>&1
    Write-Result ($LASTEXITCODE -eq 0) (Get-Label $schema) $output
}

Write-Host 'Sample instances' -ForegroundColor Cyan
foreach ($schema in $schemas) {
    $instance = Join-Path $schema.Directory.FullName 'example.json'
    if (-not (Test-Path $instance)) {
        Write-Result $false (Get-Label $schema) @('example.json is missing')
        continue
    }
    $output = & json-structure-validate --extended --allowimport --quiet $instance $schema.FullName 2>&1
    Write-Result ($LASTEXITCODE -eq 0) (Get-Label $schema) $output
}

Write-Host 'Relation resolution' -ForegroundColor Cyan
$checker = Join-Path $toolsRoot 'check-relations.py'
$python = @('py', 'python3', 'python') |
    Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } |
    Select-Object -First 1
if (-not $python) {
    Write-Host '  [skip] no Python interpreter on PATH' -ForegroundColor Yellow
}
else {
    foreach ($schema in $schemas) {
        $instance = Join-Path $schema.Directory.FullName 'example.json'
        if (Test-Path $instance) {
            $output = & $python $checker $schema.FullName $instance 2>&1
        }
        else {
            $output = & $python $checker $schema.FullName 2>&1
        }
        Write-Result ($LASTEXITCODE -eq 0) (Get-Label $schema) $output
    }
}

Write-Host ''
if ($failures -eq 0) {
    Write-Host 'All checks passed.' -ForegroundColor Green
    exit 0
}

Write-Host "$failures check(s) failed." -ForegroundColor Red
exit 1

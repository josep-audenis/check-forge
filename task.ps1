param(
    [Parameter(Position = 0)]
    [ValidateSet("build", "test", "perft", "tactics", "speed", "match", "benchmark", "cutechess", "clean")]
    [string] $Task = "build"
)

$ErrorActionPreference = "Stop"

$BuildDir = "build"
$EngineCandidates = @(
    "$BuildDir/engine/checkforge.exe",
    "$BuildDir/engine/Debug/checkforge.exe",
    "$BuildDir/engine/Release/checkforge.exe"
)

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $FilePath,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Invoke-Build {
    Invoke-Native cmake -S . -B $BuildDir
    Invoke-Native cmake --build $BuildDir
}

function Get-EnginePath {
    foreach ($Candidate in $EngineCandidates) {
        if (Test-Path $Candidate) {
            return $Candidate
        }
    }

    throw "Engine executable not found. Run './task.ps1 build' first."
}

switch ($Task) {
    "build" {
        Invoke-Build
    }
    "test" {
        Invoke-Build
        Invoke-Native ctest --test-dir $BuildDir --output-on-failure
    }
    "perft" {
        Invoke-Build
        Invoke-Native python research/run_perft.py --engine (Get-EnginePath)
    }
    "tactics" {
        Invoke-Build
        Invoke-Native python research/run_tactics.py --engine (Get-EnginePath)
    }
    "speed" {
        Invoke-Build
        Invoke-Native python research/run_speed.py --engine (Get-EnginePath)
    }
    "match" {
        Invoke-Build
        Invoke-Native python research/run_match.py --engine (Get-EnginePath)
    }
    "benchmark" {
        Invoke-Build
        $Engine = Get-EnginePath
        Invoke-Native python research/run_benchmark.py --engine $Engine
        Invoke-Native python research/evaluate_result.py results/latest.json
    }
    "cutechess" {
        Invoke-Build
        $Engine = Get-EnginePath
        Invoke-Native python research/run_cutechess.py --engine $Engine --opponent-engine $Engine
    }
    "clean" {
        if (Test-Path $BuildDir) {
            Invoke-Native cmake --build $BuildDir --target clean
        }
    }
}

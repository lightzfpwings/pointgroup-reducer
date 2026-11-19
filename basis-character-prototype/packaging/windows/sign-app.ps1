param(
    [Parameter(Mandatory=$true)][string]$Package,
    [Parameter(Mandatory=$true)][string]$Report,
    [Parameter(Mandatory=$true)][string]$SignTool,
    [string]$Thumbprint = '',
    [string]$ExpectedSignerSubject = '',
    [string]$TimestampUrl = 'http://timestamp.digicert.com',
    [switch]$MachineStore
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Keys stay in the configured certificate provider (including HSM/cloud KSPs).
# No PFX import, certificate password or trust-store modification is performed.
if ($Thumbprint -and $Thumbprint -notmatch '^[0-9a-fA-F]{40}$') {
    throw 'Expected a 40-character certificate thumbprint.'
}
if (-not $Thumbprint -and -not $ExpectedSignerSubject) {
    throw 'Pin the intended publisher with a certificate thumbprint or exact subject.'
}
$files = @('BasisCharacter.exe', 'BasisCharacter.dll')
$results = @()
foreach ($name in $files) {
    $path = Join-Path $Package $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing application binary: $name"
    }
    if ($Thumbprint) {
        $arguments = @('sign', '/sha1', $Thumbprint, '/s', 'My', '/fd', 'SHA256',
                       '/tr', $TimestampUrl, '/td', 'SHA256', '/d', 'Point Groups & Basis Functions')
        if ($MachineStore) { $arguments += '/sm' }
        & $SignTool @arguments $path
        if ($LASTEXITCODE -ne 0) { throw "SignTool signing failed: $name" }
    }
    # Default Authenticode policy validates trust and integrity; /all checks any
    # additional embedded signatures. Treat missing timestamp warnings as failure.
    & $SignTool verify /pa /all /tw $path
    if ($LASTEXITCODE -ne 0) { throw "SignTool verification failed: $name" }
    $signature = Get-AuthenticodeSignature -LiteralPath $path
    if ($signature.Status -ne 'Valid' -or $signature.SignatureType.ToString() -ne 'Authenticode') {
        throw "A valid embedded Authenticode signature is required: $name"
    }
    $certificate = $signature.SignerCertificate
    $timestamp = $signature.TimeStamperCertificate
    if ($null -eq $certificate -or $null -eq $timestamp) {
        throw "A publisher certificate and verified timestamp are required: $name"
    }
    if ($certificate.Subject -eq $certificate.Issuer) {
        throw "A self-signed publisher certificate is not accepted: $name"
    }
    if ($Thumbprint -and $certificate.Thumbprint -ine $Thumbprint) {
        throw "Unexpected application signing certificate: $name"
    }
    if ($ExpectedSignerSubject -and $certificate.Subject -cne $ExpectedSignerSubject) {
        throw "Unexpected application publisher: $name"
    }
    $results += @{
        path = $name
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        subject = $certificate.Subject
        thumbprint = $certificate.Thumbprint
        timestampSubject = $timestamp.Subject
        timestampThumbprint = $timestamp.Thumbprint
    }
}
$mode = if ($Thumbprint) { 'certificate-store' } else { 'external' }
@{
    status = 'passed'
    mode = $mode
    trustPolicy = 'Windows Authenticode'
    timestampRequired = $true
    files = $results
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Report -Encoding utf8

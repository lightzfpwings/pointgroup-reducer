param([Parameter(Mandatory=$true)][string]$Installer, [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference = 'Stop'
$signature = Get-AuthenticodeSignature -LiteralPath $Installer
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') {
    throw 'WebView2 installer must have a valid Microsoft Authenticode signature.'
}
$item = Get-Item -LiteralPath $Installer
if ($item.Length -lt 50000000) { throw 'Expected the full offline installer, not the online bootstrapper.' }
@{
    status = 'passed'
    signature = $signature.Status.ToString()
    signer = $signature.SignerCertificate.Subject
    certificateThumbprint = $signature.SignerCertificate.Thumbprint
    fileVersion = $item.VersionInfo.FileVersion
    bytes = $item.Length
    sha256 = (Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
    source = 'https://go.microsoft.com/fwlink/p/?LinkId=2124701'
} | ConvertTo-Json | Set-Content -LiteralPath $Report -Encoding utf8

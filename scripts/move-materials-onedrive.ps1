$ErrorActionPreference = 'Stop'
$repo = 'C:\GitHub\coldKode-presenter'
$destinationRoot = 'C:\Users\a1ole\OneDrive\coldKode-presenter'
$oneDriveRoot = (Resolve-Path -LiteralPath 'C:\Users\a1ole\OneDrive').Path
if (-not $destinationRoot.StartsWith($oneDriveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe destination' }
$targets = @('data', 'output')
$secrets = @()
foreach ($line in Get-Content -LiteralPath "$repo\.env") {
 if ($line -match '^\s*([^#=]+)=(.*)$') {
  $name = $Matches[1]; $rawValue = $Matches[2]
  if ($name -notmatch 'KEY|TOKEN|SECRET|PASSWORD') { continue }
  $value = $rawValue.Trim().Trim('"').Trim("'")
  if ($value.Length -ge 12) { $secrets += $value }
 }
}
$manifest = @()
foreach ($name in $targets) {
 $source = (Resolve-Path -LiteralPath (Join-Path $repo $name)).Path
 $destination = [IO.Path]::GetFullPath((Join-Path $destinationRoot $name))
 if ($source -ne "$repo\$name" -or -not $destination.StartsWith($destinationRoot+'\')) { throw 'Target validation failed' }
 if ((Get-Item -LiteralPath $source).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source already redirected' }
 if (Test-Path -LiteralPath $destination) { throw "Destination already exists: $destination" }
 $files = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
 foreach ($file in $files) {
  if ($file.Name -match '^\.env($|\.)|credentials.*\.json$|\.pem$') { throw "Sensitive file: $($file.FullName)" }
  if ($file.Extension -in @('.json','.txt','.py','.mjs','.js','.md','.yaml','.yml','.log','.ini','.xml') -and $file.Length -lt 20MB) {
   $text = [IO.File]::ReadAllText($file.FullName)
   foreach ($secret in $secrets) { if ($text.Contains($secret)) { throw "Secret detected in $($file.FullName)" } }
  }
  $manifest += [pscustomobject]@{Path=$file.FullName.Substring($repo.Length+1);Bytes=$file.Length;SHA256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
 }
}
New-Item -ItemType Directory -Path $destinationRoot | Out-Null
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$repo\tmp\onedrive-materials-manifest.json" -Encoding UTF8
foreach ($name in $targets) {
 $source = "$repo\$name"; $destination = "$destinationRoot\$name"
 Move-Item -LiteralPath $source -Destination $destination
 New-Item -ItemType Junction -Path $source -Target $destination | Out-Null
}
foreach ($entry in $manifest) {
 $target = Join-Path $destinationRoot $entry.Path
 if (-not (Test-Path -LiteralPath $target) -or (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $entry.SHA256) { throw "Verification failed: $target" }
}
[pscustomobject]@{Destination=$destinationRoot;Files=$manifest.Count;Bytes=($manifest|Measure-Object Bytes -Sum).Sum;Verified=$true} | ConvertTo-Json

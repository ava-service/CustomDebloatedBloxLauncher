# Created by: https://github.com/KickfnGIT/DebloatedBloxLauncher

param(
    [string]$Sensitivity = "",
    [string]$FPSCap = "",
    [string]$Graphics = "",
    [string]$Volume = ""
)

$robloxSettings = 'func\GlobalBasicSettings_13.xml'

if (-not (Test-Path $robloxSettings)) {
    Write-Host "ERROR: Settings file not found at $robloxSettings"
    Write-Host "Make sure Roblox has generated the file before running this script."
    exit
}

[xml]$xml = Get-Content $robloxSettings

# Sensitivity
if ($Sensitivity -ne "") {
    $sensitivity = $null
    if ([double]::TryParse($Sensitivity, [ref]$sensitivity) -and $sensitivity -ge 0.00001 -and $sensitivity -le 100) {
        $xml.SelectSingleNode("//float[@name='MouseSensitivity']").InnerText = "$sensitivity"
        $xml.SelectSingleNode("//Vector2[@name='MouseSensitivityFirstPerson']/X").InnerText = "$sensitivity"
        $xml.SelectSingleNode("//Vector2[@name='MouseSensitivityFirstPerson']/Y").InnerText = "$sensitivity"
        $xml.SelectSingleNode("//Vector2[@name='MouseSensitivityThirdPerson']/X").InnerText = "$sensitivity"
        $xml.SelectSingleNode("//Vector2[@name='MouseSensitivityThirdPerson']/Y").InnerText = "$sensitivity"
        Write-Host "Sensitivity set to: $sensitivity"
    } else {
        Write-Host "Invalid sensitivity input. Not changed."
    }
}

# FPS Cap
if ($FPSCap -ne "") {
    if ($FPSCap -match '^(inf|INF)$') {
        $fpscap = 9999999
        $xml.SelectSingleNode("//int[@name='FramerateCap']").InnerText = "$fpscap"
        Write-Host "FPS cap set to: $fpscap"
    } else {
        $fpscap = $null
        if ([int]::TryParse($FPSCap, [ref]$fpscap) -and $fpscap -ge 1 -and $fpscap -le 99999) {
            $xml.SelectSingleNode("//int[@name='FramerateCap']").InnerText = "$fpscap"
            Write-Host "FPS cap set to: $fpscap"
        } else {
            Write-Host "Invalid FPS cap input. Not changed."
        }
    }
}

# Graphics Quality
if ($Graphics -ne "") {
    if ($Graphics -match '^(1[0-9]|20|[1-9])$') {
        $xml.SelectSingleNode("//int[@name='GraphicsQualityLevel']").InnerText = "$Graphics"
        $xml.SelectSingleNode("//token[@name='SavedQualityLevel']").InnerText = "$Graphics"
        Write-Host "Graphics quality set to: $Graphics"
    } else {
        Write-Host "Invalid graphics input. Not changed."
    }
}

# Volume
if ($Volume -ne "") {
    if ($Volume -match '^(10|[1-9])$') {
        $scaledVolume = [math]::Round([double]$Volume / 10, 1)
        $xml.SelectSingleNode("//float[@name='MasterVolume']").InnerText = "$scaledVolume"
        Write-Host "Volume set to: $Volume"
    } else {
        Write-Host "Invalid volume input. Not changed."
    }
}

# Save XML
$xml.Save($robloxSettings)
Write-Host "Settings updated successfully!"

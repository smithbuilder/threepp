function Get-EvaluationSha256 {
    param([Parameter(Mandatory=$true)][string]$LiteralPath)
    # Windows PowerShell's script-module Get-FileHash can be unavailable in a
    # launcher-inherited module environment. Stream the same SHA256 with the
    # built-in framework instead; no profile/module import or policy change.
    $evaluationHashPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($LiteralPath)
    $evaluationHashStream = [IO.File]::OpenRead($evaluationHashPath)
    $evaluationHashAlgorithm = $null
    try {
        $evaluationHashAlgorithm = [Security.Cryptography.SHA256]::Create()
        return [BitConverter]::ToString($evaluationHashAlgorithm.ComputeHash($evaluationHashStream)).Replace('-','')
    } finally {
        if ($evaluationHashAlgorithm) { $evaluationHashAlgorithm.Dispose() }
        $evaluationHashStream.Dispose()
    }
}

# PowerShell pre-commit hook (Windows)
# To enable locally: git config core.hooksPath .githooks

$proc = Start-Process -FilePath "python" -ArgumentList "tools/ci_validate.py --json posts/blog-posts.json --warn-only" -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Host "Validator found problems. Commit aborted. (Run with --warn-only to only warn.)" -ForegroundColor Red
    exit $proc.ExitCode
}
exit 0

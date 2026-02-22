# PowerShell runner for repo cleanup automation.
# Usage: run in repo root. To allow destructive rewrite, set $env:CONFIRM_REWRITE = 'true' OR create a file named .confirm_rewrite
set-StrictMode -Version Latest
$RepoRoot = Resolve-Path "."
Write-Output "Repo automation starting at $RepoRoot"
# 1) Basic checks
git --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Output "git not found. Aborting."; exit 1 }
python --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Output "python not found. Aborting."; exit 1 }

# Logging
$log = Join-Path $RepoRoot "automation.log"
"$(Get-Date -Format s) INFO Starting automation" | Out-File -FilePath $log -Encoding utf8 -Append

# 2) Create backup branch
$backup = "backup/pre-clean-" + (Get-Date -Format "yyyyMMddHHmmss")
git checkout -b $backup
git push -u origin $backup
"$(Get-Date -Format s) INFO Created backup $backup" | Out-File -FilePath $log -Encoding utf8 -Append

# 3) Ensure working tree clean (only stage local changes we intend to commit)
git add -A
git reset --hard HEAD
"$(Get-Date -Format s) INFO Reset working tree" | Out-File -FilePath $log -Encoding utf8 -Append

# 4) Generate the plan
if (-not (Test-Path ".\\all_objects.txt")) {
    Write-Output "Generating all_objects.txt (may take a moment)..."
    git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' > all_objects.txt
}
python tools/automation/generate_plan.py | Tee-Object -Variable out
"$(Get-Date -Format s) INFO Generated filter plan" | Out-File -FilePath $log -Encoding utf8 -Append

# 5) Update .gitignore/.gitattributes with LFS recommendations (no push yet)
if (Test-Path "lfs_candidates.txt") {
    $gitattributes = ".gitattributes"
    $gitignore = ".gitignore"
    Get-Content lfs_candidates.txt | ForEach-Object {
        $pattern = $_.Trim()
        if ($pattern -and -not (Select-String -Path $gitattributes -SimpleMatch $pattern -Quiet)) {
            "\$pattern filter=lfs diff=lfs merge=lfs -text" | Out-File -FilePath $gitattributes -Append -Encoding utf8
        }
        if ($pattern -and -not (Select-String -Path $gitignore -SimpleMatch $pattern -Quiet)) {
            "$pattern" | Out-File -FilePath $gitignore -Append -Encoding utf8
        }
    }
    "Added LFS candidate patterns to .gitattributes and .gitignore" | Out-File -FilePath $log -Encoding utf8 -Append
}

# 6) Show summary to log
Get-Content filter-repo-plan.json | Out-File -FilePath $log -Encoding utf8 -Append

# 7) DRY-RUN mode:
$plan = Get-Content filter-repo-remove-paths.txt -ErrorAction SilentlyContinue
if (-not $plan) {
    "$(Get-Date -Format s) INFO Dry-run: nothing to remove" | Out-File -FilePath $log -Encoding utf8 -Append
} else {
    "$(Get-Date -Format s) INFO Dry-run removal list:" | Out-File -FilePath $log -Encoding utf8 -Append
    Get-Content filter-repo-remove-paths.txt | Out-File -FilePath $log -Encoding utf8 -Append
}

# 8) Guarded actual rewrite step
$confirm = $false
# use explicit grouping for boolean expression to avoid parser issues
if ( ($env:CONFIRM_REWRITE -eq 'true') -or (Test-Path '.confirm_rewrite') ) { $confirm = $true }
if (-not $confirm) {
    Write-Output "Rewrite is gated. To run the destructive history rewrite set the environment variable CONFIRM_REWRITE=true or create a file named .confirm_rewrite in repo root."
    "$(Get-Date -Format s) INFO Destructive rewrite NOT executed (guarded)" | Out-File -FilePath $log -Encoding utf8 -Append
    # Write final report and exit safe
    git count-objects -vH | Out-File -FilePath automation_report.md -Encoding utf8 -Append
    exit 0
}

# 9) If confirmed, proceed (this part will rewrite history)
# Ensure git-filter-repo exists
try {
    git filter-repo --version > $null 2>&1
} catch {
    Write-Output "git-filter-repo not found. Attempting pip install git-filter-repo"
    python -m pip install git-filter-repo
}
# Execute removal using paths file (invert paths)
if (Test-Path "filter-repo-remove-paths.txt") {
    Write-Output "Executing git-filter-repo to remove listed paths (this rewrites history)"
    # Warning: destructive. We use --force because user confirmed.
    git filter-repo --paths-from-file filter-repo-remove-paths.txt --invert-paths --force
    git gc --aggressive --prune=now
    git repack -a -d --max-pack-size=100m
    git push --force-with-lease origin HEAD:refs/heads/cleaned-history
    "$(Get-Date -Format s) INFO Completed filter-repo rewrite and pushed cleaned-history" | Out-File -FilePath $log -Encoding utf8 -Append
    # Create a PR using GH token if available
    if ($env:GITHUB_TOKEN) {
        $repo = (git remote get-url origin) -replace 'https://github.com/','' -replace '^git@github.com:','' -replace '\.git$',''
        $title = 'chore: cleaned repo history (automated)'
        $body = 'Automated history rewrite removing large tracked files. Backup branch: ' + $backup
        # use GitHub API
        $json = @{title=$title; head='cleaned-history'; base='main'; body=$body} | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/pulls" -Method Post -Headers @{Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent'='automation'} -Body $json
    }
}

"$(Get-Date -Format s) INFO Automation finished" | Out-File -FilePath $log -Encoding utf8 -Append

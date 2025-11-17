# Contributing

Guidelines for images and preflight checks

- Do NOT commit raw/original high-resolution images to this repository. Raw images belong in `raw-images/` on your local machine or in external storage (cloud or archive). Adding many large binaries will bloat the git repo.

- This repo stores optimized derivatives (thumbnails / hero images) under `blog-images/thumbs/`. Those are safe to commit and are used by the static site.

- If you must keep originals in the repo, use Git LFS for them. Example:

  ```bash
  git lfs install
  git lfs track "raw-images/*"
  git add .gitattributes
  git commit -m "Track raw images with LFS"
  ```

- Preflight validation

  A validator script is available at `tools/ci_validate.py`. It checks `posts/blog-posts.json` for consistency, verifies referenced image files exist, warns about filenames with spaces/capital letters, and can optionally check image dimensions and file size.

  Run locally with:

  ```bash
  python -m pip install pillow
  python tools/ci_validate.py --json posts/blog-posts.json
  ```

  In CI the project runs the same script automatically on PRs.

- Image naming

  Use slugified, lowercase file names with hyphens (e.g., `whisky-and-the-sun-800.jpg`). Avoid spaces and uppercase to prevent cross-platform issues.

- If you add or regenerate thumbnails, update `posts/blog-posts.json` with the correct `thumb` and `hero` fields.

If you have questions about the pipeline or need assistance moving large files to LFS, open a GitHub issue, add a card to the project's GitHub board, or ping the maintainer.

Pre-commit hook (optional)

You can enable a local pre-commit hook that runs the validator before every commit.

On Unix/macOS:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

On Windows PowerShell:

```powershell
git config core.hooksPath .githooks
# Ensure .githooks\pre-commit.ps1 is executable by your policy
```

The hook runs `python tools/ci_validate.py --warn-only` so it will warn you about issues but won't block the commit by default. To make the hook fail the commit on warnings, edit the hook to call the validator without `--warn-only`.

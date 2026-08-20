# CI workflow

`ci.yml` is the GitHub Actions pipeline (backend pytest + migration check,
frontend vitest + build, and a Playwright E2E job).

The sandbox GitHub token does not have the `workflows` permission, so this
file lives here instead of `.github/workflows/`. To activate it on a machine
with normal credentials:

```bash
mkdir -p .github/workflows
cp ci/ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml && git commit -m "ci: activate pipeline" && git push
```

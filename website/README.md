# CanIRunLLM marketing site

A static landing page (no build step, no framework) explaining
CanIRunLLM and linking to the downloads. Lives in this subdirectory
so it can be deployed independently of the Python package.

## Deploy on Vercel

1. Go to https://vercel.com/new and import the `CaniRunLLM` GitHub
   repository (connect your GitHub account if you haven't already).
2. When Vercel asks for the **Root Directory**, set it to `website`.
3. Framework preset: **Other** (it's plain static HTML/CSS/JS — no
   build command needed).
4. Click Deploy.

Every push to `main` that touches this folder will auto-redeploy.

## The "Test Now" download button

It links to `download.html`, a dedicated download page, rather than
triggering the `.exe` download directly — clicking a link on the
landing page and immediately getting a browser download prompt with
no context in between felt abrupt, and a real download page gives a
place to explain what happens next and let people verify the release
themselves first.

`download.html`'s actual button points at:

```
https://github.com/jashwanthsai678/CaniRunLLM/releases/latest/download/CanIRunLLM.exe
```

This is a stable GitHub URL — it always resolves to the file named
`CanIRunLLM.exe` attached to whichever release is currently marked
"latest." You don't need to update this link when you cut a new
release; you just need every release to keep attaching the built
exe under that exact filename (see `../packaging/README.md` for how
to build it). The Install section's `.exe` tab on the main page links
to the same `download.html` page, for consistency.

## Local preview

```bash
cd website
python -m http.server 8000
# open http://localhost:8000
```

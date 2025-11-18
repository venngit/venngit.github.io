# Post Templates

This folder contains the HTML templates and individual post pages used by the site.

Canonical template
- `posts/post-template.html`: the single canonical template used for new post generation.
  - Placeholders used by automation:
    - `{{TITLE}}` — the post title inserted by `tools/add_image.py` when creating a new post file.
    - `{{IMAGE}}` — the image URL used by the template's `<img id="post-image">` element.
  - Runtime behavior:
    - `scripts/post-meta.js` populates the visible `#post-title` and `#post-date` from `posts/blog-posts.json`.
    - If a post has `hasMap: true`, `post-meta.js` will call `initMap(coordinates)` (the template includes a generic `initMap` implementation).

Legacy templates
- `posts/post-template-no-map.html` and `posts/post-template-has-map.html` are retained for backward compatibility. They are effectively equivalent to the canonical template and can be removed when you are comfortable with the migration.

Tooling
- `tools/add_image.py` creates new posts and uses `posts/post-template.html` by default.
- `scripts/post-meta.js` centralizes metadata population (title, date, image, map invocation) so individual post files can remain minimal.

Guidelines
- To change layout for all new posts, update `posts/post-template.html`.
- To create a manual post that still benefits from `post-meta.js`, include the `#post-title`, `#post-date`, and `#post-image` elements and a reference to `/scripts/post-meta.js`.

Example minimal post shell
```html
<!doctype html>
<html>
  <head>...</head>
  <body>
    <h2 id="post-title">Loading Post...</h2>
    <p id="post-date">Published on DATE</p>
    <img id="post-image" src="../blog-images/example.jpg" />
    <script src="/scripts/post-meta.js"></script>
  </body>
</html>
```

Migration
- If you want to convert existing full-page post files into minimal shells that rely on the single template + `post-meta.js`, we can create a migration script to rewrite files safely. Ask for this when ready.

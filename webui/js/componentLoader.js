// Minimal HTML component loader that executes inline <script> tags
// Exposes window.loadHtmlComponent(path, targetEl)

window.loadHtmlComponent = async function loadHtmlComponent(path, targetEl) {
  const res = await fetch(path);
  const html = await res.text();

  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");

  // Extract and execute scripts
  const scripts = Array.from(doc.querySelectorAll("script"));
  scripts.forEach((s) => s.parentNode && s.parentNode.removeChild(s));

  // Insert HTML content (without scripts)
  targetEl.innerHTML = doc.body.innerHTML;

  // Execute scripts in order
  for (const script of scripts) {
    const newScript = document.createElement("script");
    // Copy attributes (type, module, etc.)
    for (const attr of script.attributes) {
      newScript.setAttribute(attr.name, attr.value);
    }
    if (script.src) {
      newScript.src = script.src;
    } else {
      newScript.textContent = script.textContent || "";
    }
    document.head.appendChild(newScript);
  }
};




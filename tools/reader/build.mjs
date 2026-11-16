import { copyFile, mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import MarkdownIt from "markdown-it";
import { mathjax } from "mathjax-full/js/mathjax.js";
import { TeX } from "mathjax-full/js/input/tex.js";
import "mathjax-full/js/input/tex/ams/AmsConfiguration.js";
import "mathjax-full/js/input/tex/boldsymbol/BoldsymbolConfiguration.js";
import { liteAdaptor } from "mathjax-full/js/adaptors/liteAdaptor.js";
import { RegisterHTMLHandler } from "mathjax-full/js/handlers/html.js";
import { STATE } from "mathjax-full/js/core/MathItem.js";
import { SerializedMmlVisitor } from "mathjax-full/js/core/MmlTree/SerializedMmlVisitor.js";

const repo = new URL("../../", import.meta.url);
const repoPath = fileURLToPath(repo);
const bundle = "Volterra_Wiki_00-06_完整合订版_GitHub图床.md";
const repositoryUrl = "https://github.com/EXCILLEX-Marisa/volterra-wiki";
const rawFigures = "https://raw.githubusercontent.com/EXCILLEX-Marisa/volterra-wiki/main/figures/";
const output = resolve(process.argv[2] ?? "dist");
const source = await readFile(new URL("downloads/" + bundle, repo), "utf8");

RegisterHTMLHandler(liteAdaptor());
const input = new TeX({
  packages: ["base", "ams", "boldsymbol"],
  formatError: (_, error) => { throw Error(error.message); },
});
const document = mathjax.document("", {InputJax: input});
const serializer = new SerializedMmlVisitor();
const math = new Map();

function typeset(value, display) {
  const tex = value.trim();
  const key = JSON.stringify([display, tex]);
  if (!math.has(key)) {
    try {
      const compiled = document.convert(tex, {display, end: STATE.COMPILED});
      math.set(key, serializer.visitTree(compiled).replace(/^\s+</gm, "<"));
    } catch (error) {
      throw Error(`Invalid TeX: ${tex}\n${error.message}`, {cause: error});
    }
  }
  return math.get(key);
}

let inlineCount = 0;
let displayCount = 0;
const figures = new Set();
const md = new MarkdownIt({html: false, linkify: true});
md.inline.ruler.before("backticks", "volterra_math", (state, silent) => {
  if (state.src[state.pos] !== "$") return false;
  const match = /^\$`([^`\n]+)`\$/.exec(state.src.slice(state.pos));
  if (!match) return false;
  if (!silent) state.push("volterra_math", "math", 0).content = match[1];
  state.pos += match[0].length;
  return true;
});
md.inline.ruler.before("html_inline", "volterra_line_break", (state, silent) => {
  if (!state.src.startsWith("<br>", state.pos)) return false;
  if (!silent) state.push("hardbreak", "br", 0);
  state.pos += "<br>".length;
  return true;
});
md.renderer.rules.volterra_math = (tokens, index) => {
  inlineCount++;
  return `<span class="inline-equation">${typeset(tokens[index].content, false)}</span>`;
};
const renderFence = md.renderer.rules.fence;
md.renderer.rules.fence = (tokens, index, ...args) => {
  if (tokens[index].info.trim() !== "math") return renderFence(tokens, index, ...args);
  displayCount++;
  return `<div class="equation">${typeset(tokens[index].content, true)}</div>\n`;
};
const renderImage = md.renderer.rules.image;
md.renderer.rules.image = (tokens, index, ...args) => {
  const image = tokens[index];
  const src = image.attrGet("src");
  if (src.startsWith(rawFigures)) {
    const filename = decodeURIComponent(src.slice(rawFigures.length));
    if (basename(filename) !== filename || !filename.endsWith(".svg")) {
      throw Error("Invalid figure filename: " + filename);
    }
    figures.add(filename);
    image.attrSet("src", "figures/" + encodeURIComponent(filename));
    image.attrSet("loading", "lazy");
    image.attrSet("decoding", "async");
    image.attrSet("width", "1600");
    image.attrSet("height", "980");
  } else if (src.startsWith("figures/")) {
    throw Error("The consolidated edition must use GitHub raw figure URLs; found relative path: " + src);
  }
  return renderImage(tokens, index, ...args);
};
md.renderer.rules.table_open = () => '<div class="table-scroll"><table>\n';
md.renderer.rules.table_close = () => "</table></div>\n";

const tokens = md.parse(source, {});
const chapters = [];
const headingIds = new Set();
for (let i = 0; i < tokens.length; i++) {
  const heading = tokens[i];
  if (heading.type !== "heading_open") continue;
  const title = tokens[i + 1].content;
  if (heading.tag === "h1") {
    const chapter = /^(0[0-6]) /.exec(title)?.[1];
    if (chapter) {
      const id = `chapter-${chapter}`;
      chapters.push({id, title});
      heading.attrSet("id", id);
    } else {
      heading.attrSet("id", "title");
    }
  } else {
    const section = /^(\d+(?:\.\d+)+) /.exec(title)?.[1];
    if (section) {
      const id = `section-${section.replaceAll(".", "-")}`;
      if (headingIds.has(id)) throw Error(`Duplicate section: ${section}`);
      headingIds.add(id);
      heading.attrSet("id", id);
    }
  }
}
if (chapters.map(chapter => chapter.id).join(",") !== "chapter-00,chapter-01,chapter-02,chapter-03,chapter-04,chapter-05,chapter-06") {
  throw Error("The combined edition must include chapters 00–06 in order.");
}

// The first heading is shown in the page header with the reading controls.
const title = tokens[1].content;
const body = md.renderer.render(tokens.slice(3), md.options, {});
const chapterFiles = (await readdir(repoPath)).filter(name => /^0[0-6]_.*\.md$/.test(name));
function normalizeChapter(content) {
  return content
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "![$1](FIGURE)")
    .replace(/^\[在线阅读本章（完整合订版）\]\([^)]+\)\s*$/gm, "")
    .replace(/^\*\*章节导航：\*\*.*$/gm, "")
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
const chapterMatches = [...source.matchAll(/^# (0[0-6]) .+$/gm)];
if (chapterMatches.length !== 7) {
  throw Error("The consolidated edition must include seven chapter headings; found " + chapterMatches.length + ".");
}
for (let i = 0; i < chapterMatches.length; i++) {
  const id = chapterMatches[i][1];
  const filename = chapterFiles.find(name => name.startsWith(id + "_"));
  if (!filename) throw Error("Missing source chapter file for chapter " + id + ".");
  const end = chapterMatches[i + 1]?.index ?? source.length;
  const bundledChapter = source.slice(chapterMatches[i].index, end);
  const sourceChapter = await readFile(join(repoPath, filename), "utf8");
  if (normalizeChapter(bundledChapter) !== normalizeChapter(sourceChapter)) {
    throw Error("Consolidated chapter " + id + " is out of sync with " + filename + ". Rebuild the bundle from the chapter source.");
  }
}
function countMath(content) {
  return [...content.matchAll(/\$`[^`\r\n]+`\$|^(?:> )?```math[ \t]*\r?$/gm)].length;
}
let expected = 0;
for (const filename of chapterFiles) {
  expected += countMath(await readFile(join(repoPath, filename), "utf8"));
}
if (expected !== inlineCount + displayCount || expected !== countMath(source)) {
  throw Error(`Formula count mismatch: chapters ${expected}, preview ${inlineCount + displayCount}.`);
}
const figureFiles = new Set((await readdir(join(repoPath, "figures"))).filter(name => name.endsWith(".svg")));
const missingFigures = [...figures].filter(filename => !figureFiles.has(filename));
const unreferencedFigures = [...figureFiles].filter(filename => !figures.has(filename));
if (missingFigures.length || unreferencedFigures.length) {
  throw Error(
    "Figure inventory mismatch: " + figures.size + " referenced, " + figureFiles.size + " stored. " +
    "Missing files: " + (missingFigures.join(", ") || "none") + ". " +
    "Unreferenced files: " + (unreferencedFigures.join(", ") || "none") + "."
  );
}
const escape = md.utils.escapeHtml;
const toc = chapters.map(({id, title}) => `<li><a href="#${id}">${escape(title)}</a></li>`).join("\n");
const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Volterra Wiki 00—06 完整合订版，附公式与教学图。">
  <title>${escape(title)}</title>
  <link rel="stylesheet" href="reader.css">
</head>
<body>
  <header id="top">
    <h1 id="title">${escape(title)}</h1>
    <p class="links"><a href="${encodeURIComponent(bundle)}" download>下载 Markdown</a><a href="${repositoryUrl}">GitHub 仓库</a></p>
    <nav aria-label="章节目录"><ul>${toc}</ul></nav>
  </header>
  <main>${body}</main>
  <footer><a href="#top">返回目录</a></footer>
</body>
</html>
`;
await mkdir(join(output, "figures"), {recursive: true});
await Promise.all([
  writeFile(join(output, "index.html"), html, "utf8"),
  writeFile(join(output, bundle), source, "utf8"),
  copyFile(join(dirname(fileURLToPath(import.meta.url)), "reader.css"), join(output, "reader.css")),
  ...[...figures].map(filename => copyFile(join(repoPath, "figures", filename), join(output, "figures", filename))),
]);
console.log(`Built 7 synchronized chapters, ${inlineCount + displayCount} formulas and ${figures.size} verified figures.`);

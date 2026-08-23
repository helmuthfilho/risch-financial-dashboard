// REPL driver for the risch-financial-dashboard Next.js dev server.
// Headless Chromium via Playwright. Designed for agents: wrap in tmux,
// send-keys commands one line at a time, capture-pane for output.
//
// Used because `chromium-cli` was not available in this environment; this
// driver mirrors its command vocabulary (nav / wait-for / screenshot /
// click / fill / press / console) using plain Playwright `chromium`.
import { chromium } from "playwright";
import * as readline from "node:readline";
import * as fs from "node:fs";
import * as path from "node:path";

const SHOT_DIR = process.env.SCREENSHOT_DIR || "/tmp/shots";
fs.mkdirSync(SHOT_DIR, { recursive: true });

let browser = null;
let page = null;
const consoleErrors = [];

const COMMANDS = {
  async launch() {
    if (browser) return console.log("already launched");
    browser = await chromium.launch({ args: ["--no-sandbox"] });
    const context = await browser.newContext();
    page = await context.newPage();
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(String(err)));
    console.log("launched.");
  },

  async nav(url) {
    if (!page) return console.log("ERROR: launch first");
    await page.goto(url, { waitUntil: "domcontentloaded" });
    console.log("nav", url, "→ OK");
  },

  // wait-for text=Foo   OR   wait-for css=.some-selector   OR a bare CSS selector
  async "wait-for"(arg) {
    if (!page) return console.log("ERROR: launch first");
    try {
      if (arg.startsWith("text=")) {
        await page.getByText(arg.slice(5)).first().waitFor({ timeout: 10_000 });
      } else {
        const sel = arg.startsWith("css=") ? arg.slice(4) : arg;
        await page.waitForSelector(sel, { timeout: 10_000 });
      }
      console.log("found:", arg);
    } catch {
      console.log("TIMEOUT:", arg);
    }
  },

  async screenshot(name) {
    if (!page) return console.log("ERROR: launch first");
    const f = path.join(SHOT_DIR, (name || `ss-${Date.now()}`) + ".png");
    await page.screenshot({ path: f, fullPage: true });
    console.log("screenshot:", f);
  },

  // click text=Gastos   OR   click css=nav a[href="/gastos"]
  async click(arg) {
    if (!page) return console.log("ERROR: launch first");
    try {
      if (arg.startsWith("text=")) {
        await page.getByText(arg.slice(5)).first().click();
      } else {
        const sel = arg.startsWith("css=") ? arg.slice(4) : arg;
        await page.click(sel);
      }
      console.log("click", arg, "→ OK");
    } catch (e) {
      console.log("click", arg, "→ ERROR:", e.message.split("\n")[0]);
    }
  },

  async fill(rest) {
    if (!page) return console.log("ERROR: launch first");
    const [sel, ...words] = rest.split(/\s+/);
    await page.fill(sel, words.join(" "));
    console.log("fill", sel, "→ OK");
  },

  async press(key) {
    if (!page) return console.log("ERROR: launch first");
    await page.keyboard.press(key);
    console.log("press", key, "→ OK");
  },

  async text(sel) {
    if (!page) return console.log("ERROR: launch first");
    const out = await page.evaluate(
      (s) =>
        (s ? document.querySelector(s) : document.body)?.innerText ?? "(null)",
      sel || null,
    );
    console.log(out);
  },

  async eval(expr) {
    if (!page) return console.log("ERROR: launch first");
    try {
      console.log(JSON.stringify(await page.evaluate(expr)));
    } catch (e) {
      console.log("ERROR:", e.message);
    }
  },

  async url() {
    if (!page) return console.log("ERROR: launch first");
    console.log(page.url());
  },

  // emulate-color-scheme dark   OR   emulate-color-scheme light
  // Sets the actual prefers-color-scheme media feature (unlike editing CSS
  // vars via `eval`, this also flips Tailwind `dark:` variant classes).
  async "emulate-color-scheme"(scheme) {
    if (!page) return console.log("ERROR: launch first");
    await page.emulateMedia({ colorScheme: scheme });
    console.log("emulate-color-scheme", scheme, "→ OK");
  },

  console(arg) {
    if (arg === "--errors" || arg === "") {
      if (consoleErrors.length === 0) console.log("no console errors");
      else consoleErrors.forEach((e) => console.log("ERR:", e));
    }
  },

  async quit() {
    if (browser) await browser.close().catch(() => {});
    browser = null;
    page = null;
  },
  help() {
    console.log("commands:", Object.keys(COMMANDS).join(", "));
  },
};

const stdin = fs.createReadStream(null, { fd: fs.openSync("/dev/stdin", "r") });
const rl = readline.createInterface({
  input: stdin,
  output: process.stdout,
  prompt: "driver> ",
});

// readline emits "line" for every buffered line as soon as it arrives (e.g. a
// whole heredoc at once) without waiting for the previous async handler to
// finish — so commands must be serialized through a queue, or "launch" and
// "nav" race and "nav" runs before the browser exists.
let queue = Promise.resolve();

async function runLine(line) {
  const [cmd, ...rest] = line.trim().split(/\s+/);
  if (!cmd) return rl.prompt();
  const fn = COMMANDS[cmd];
  if (!fn) {
    console.log("unknown:", cmd, "— try: help");
    return rl.prompt();
  }
  try {
    await fn(rest.join(" "));
  } catch (e) {
    console.log("ERROR:", e.message);
  }
  if (cmd === "quit") {
    rl.close();
    process.exit(0);
  }
  rl.prompt();
}

rl.on("line", (line) => {
  queue = queue.then(() => runLine(line));
});
rl.on("close", async () => {
  await queue;
  await COMMANDS.quit();
  process.exit(0);
});

console.log(
  'risch-financial-dashboard driver — "help" for commands, "launch" to start',
);
rl.prompt();

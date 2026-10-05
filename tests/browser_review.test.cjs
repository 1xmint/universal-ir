// Run real frontend code against a small DOM and a scripted credential transport.
// No browser, authenticator, or person is simulated as authenticated authority.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function page({failAt, framed = false} = {}) {
  const nodes = new Map();
  function element() {
    return {hidden: false, disabled: false, checked: false, textContent: "", listeners: {}, children: [],
      addEventListener(name, action) { this.listeners[name] = action; },
      replaceChildren() { this.children = []; }, append(...values) { this.children.push(...values); },
      set innerHTML(_) { throw new Error("Untrusted HTML insertion"); }};
  }
  const node = id => { if (!nodes.has(id)) nodes.set(id, element()); return nodes.get(id); };
  const calls = [], credentials = [];
  const binary = Uint8Array.from([1, 2, 3]);
  const encoded = Buffer.from(binary).toString("base64url");
  const statement = "Keep tenants apart. <script>attack()</script>";
  const review = {project_id: "sample", preparation_id: "exact-preparation", candidate: {record: {body: {
    text: statement, scope: ["."], origin: {actor_id: "alice", event_id: "event"}, supersedes: [], state: "active", evidence: []}}, evaluation: {evidence_status: "unknown"}}, transition: {meaning: "structural_only"}, coverage: {complete: false, gaps: ["unknown semantics"]}};
  const credential = {id: "AQID", rawId: binary.buffer, type: "public-key", response: {
    clientDataJSON: binary.buffer, attestationObject: binary.buffer, authenticatorData: binary.buffer, signature: binary.buffer, userHandle: null}, getClientExtensionResults: () => ({})};
  const window = {isSecureContext: true};
  window.self = window; window.top = framed ? {} : window;
  const context = vm.createContext({window, location: {hash: "#" + "a".repeat(43)}, history: {replaceState(...args) { calls.push(["history", args]); }},
    document: {getElementById: node, createElement: element}, Uint8Array, atob, btoa, structuredClone,
    navigator: {credentials: {
      create: async options => { credentials.push(["create", options]); return credential; },
      get: async options => { credentials.push(["get", options]); return credential; }}},
    fetch: async (url, options) => {
      calls.push([url, JSON.parse(options.body), options]);
      if (url === failAt) return {ok: false, json: async () => ({error: {code: "stale_preparation"}})};
      const responses = {
        "/session": {stage: "new", review},
        "/register/options": {options: {publicKey: {challenge: encoded, user: {id: encoded}, pubKeyCredParams: [{type: "public-key", alg: -7}]}}},
        "/register/complete": {status: "registered_for_demo"},
        "/review/options": {options: {publicKey: {challenge: encoded, allowCredentials: [{type: "public-key", id: encoded}]}}, request: {expires_at: "soon"}, review},
        "/review/complete": {authority: {writes: false, acceptance: "not_established"}}, "/cancel": {status: "cancelled"}};
      return {ok: true, json: async () => structuredClone(responses[url])};
    }});
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../examples/browser-review/review.js"), "utf8"), context);
  const settled = () => new Promise(resolve => setImmediate(resolve));
  const click = async id => { node(id).listeners.click(); await settled(); };
  return {node, calls, credentials, statement, settled, click};
}

test("exact review renders as text and capability stays in authorization header", async () => {
  const p = page(); await p.settled();
  assert.equal(p.node("statement").textContent, p.statement);
  assert.match(p.node("complete").textContent, /unknown semantics/);
  assert.equal(p.node("approve").disabled, true);
  const request = p.calls.find(item => item[0] === "/session");
  assert.deepEqual(request[1], {});
  assert.equal(request[2].headers.Authorization, "Bearer " + "a".repeat(43));
  assert.equal(request[2].credentials, "omit");
  assert.equal(p.calls[0][0], "history");
});

test("registration and acknowledged review convert binary transports and close", async () => {
  const p = page(); await p.settled();
  await p.click("register"); await p.click("review");
  assert.equal(p.node("approve").disabled, true);
  p.node("ack").checked = true; p.node("ack").listeners.change();
  assert.equal(p.node("approve").disabled, false);
  await p.click("approve");
  assert.equal(p.credentials[0][1].publicKey.challenge.constructor, Uint8Array);
  assert.equal(p.credentials[0][1].publicKey.user.id.constructor, Uint8Array);
  assert.equal(p.credentials[1][1].publicKey.allowCredentials[0].id.constructor, Uint8Array);
  assert.equal(p.calls.find(item => item[0] === "/review/complete")[1].response.userHandle, null);
  assert.match(p.node("result").textContent, /not_established/);
  assert.equal(p.node("approve").disabled, true);
  assert.match(p.node("status").textContent, /No knowledge was accepted/);
});

test("new review clears acknowledgment and stale result disables the ceremony", async () => {
  const p = page({failAt: "/review/complete"}); await p.settled();
  await p.click("register"); await p.click("review");
  p.node("ack").checked = true;
  await p.click("review");
  assert.equal(p.node("ack").checked, false);
  p.node("ack").checked = true; p.node("ack").listeners.change();
  await p.click("approve");
  assert.match(p.node("status").textContent, /stale_preparation/);
  assert.equal(p.node("approve").disabled, true);
  assert.equal(p.node("review").disabled, true);
});

test("cancellation closes controls and framed interface sends no project request", async () => {
  const p = page(); await p.settled(); await p.click("cancel");
  assert.match(p.node("status").textContent, /Session cancelled/);
  assert.equal(p.node("cancel").disabled, true);
  const framed = page({framed: true}); await framed.settled();
  assert.equal(framed.calls.filter(item => item[0] === "/session").length, 0);
  assert.match(framed.node("status").textContent, /top-level/);
});

"use strict";

const byId = id => document.getElementById(id);
const token = location.hash.slice(1);
history.replaceState(null, "", "/");
let currentReview;
let busy = false;
let ended = false;
const decode = value => Uint8Array.from(atob(value.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - value.length % 4) % 4)), c => c.charCodeAt(0));
const encode = buffer => btoa(String.fromCharCode(...new Uint8Array(buffer))).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
const json = value => JSON.stringify(value, null, 2);

async function call(path, payload = {}) {
  const response = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json", "Authorization": "Bearer " + token}, body: JSON.stringify(payload), cache: "no-store", credentials: "omit"});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.code || "Request failed");
  return result;
}

function controls() {
  byId("register").disabled = busy || ended || Boolean(currentReview);
  byId("review").disabled = busy || ended || !byId("register").hidden;
  byId("approve").disabled = busy || ended || !currentReview || !byId("ack").checked;
  byId("cancel").disabled = busy || ended;
}

function showReview(review) {
  const record = review.candidate.record;
  byId("identities").replaceChildren();
  for (const [label, value] of Object.entries({Project: review.project_id, Actor: record.body.origin.actor_id, Event: record.body.origin.event_id, Preparation: review.preparation_id})) {
    const dt = document.createElement("dt"), dd = document.createElement("dd");
    dt.textContent = label; dd.textContent = value;
    byId("identities").append(dt, dd);
  }
  byId("statement").textContent = record.body.text;
  byId("scope").textContent = json(record.body.scope);
  const evaluation = review.candidate.evaluation, transition = review.transition;
  byId("evidence").textContent = [
    "Record state: " + record.body.state,
    "Attribution: " + evaluation.attribution + " / " + evaluation.disposition,
    "Evidence: " + evaluation.evidence_status + " (" + record.body.evidence.length + " references)",
    "Transition: " + transition.operation + " / " + transition.meaning,
    "Competing heads after this proposal: " + transition.would_leave_competing_heads,
    "Supersedes: " + json(record.body.supersedes),
    "Coverage: " + (review.coverage.complete ? "complete for supported inspection" : "has gaps") + "; execution semantics: " + review.coverage.semantics,
    "Inspect the complete review below for evidence, affected heads, omissions, and freshness."
  ].join("\n");
  byId("complete").textContent = json(review);
  byId("proposal").hidden = false;
}

async function perform(action) {
  if (busy || ended) return;
  busy = true; controls();
  try { await action(); }
  catch (error) {
    byId("status").textContent = error.name === "NotAllowedError" ? "Authentication cancelled or unavailable. You can start the step again." : "Stopped: " + error.message;
    if (["stale_preparation", "session_expired", "ceremony_finished"].includes(error.message)) ended = true;
  }
  finally { busy = false; controls(); }
}

byId("register").addEventListener("click", () => perform(async () => {
  const transport = await call("/register/options");
  const options = transport.options.publicKey;
  options.challenge = decode(options.challenge);
  options.user.id = decode(options.user.id);
  if (options.excludeCredentials) for (const item of options.excludeCredentials) item.id = decode(item.id);
  const credential = await navigator.credentials.create({publicKey: options});
  await call("/register/complete", {id: credential.id, rawId: encode(credential.rawId), type: credential.type,
    response: {clientDataJSON: encode(credential.response.clientDataJSON), attestationObject: encode(credential.response.attestationObject)}, clientExtensionResults: credential.getClientExtensionResults()});
  byId("register").hidden = true;
  byId("status").textContent = "Temporary credential registered. Prepare and review the exact proposal before authenticating it.";
}));

byId("review").addEventListener("click", () => perform(async () => {
  currentReview = await call("/review/options");
  showReview(currentReview.review);
  byId("ack").checked = false;
  byId("expires").textContent = "This request expires at " + currentReview.request.expires_at + ". Prepare again if it expires.";
  byId("approval").hidden = false;
  byId("status").textContent = "Read the exact proposal below. Authentication verifies this review only; nothing will be written.";
}));

byId("ack").addEventListener("change", controls);
byId("approve").addEventListener("click", () => perform(async () => {
  if (!byId("ack").checked || !currentReview) return;
  const options = structuredClone(currentReview.options.publicKey);
  options.challenge = decode(options.challenge);
  for (const item of options.allowCredentials) item.id = decode(item.id);
  const credential = await navigator.credentials.get({publicKey: options});
  const result = await call("/review/complete", {id: credential.id, rawId: encode(credential.rawId), type: credential.type,
    response: {clientDataJSON: encode(credential.response.clientDataJSON), authenticatorData: encode(credential.response.authenticatorData), signature: encode(credential.response.signature), userHandle: credential.response.userHandle ? encode(credential.response.userHandle) : null}, clientExtensionResults: credential.getClientExtensionResults()});
  ended = true;
  byId("status").textContent = "Assertion verified for this exact review. The demo session is closed. No knowledge was accepted.";
  byId("outcome").hidden = false;
  byId("result").textContent = json(result);
}));

byId("cancel").addEventListener("click", () => perform(async () => {
  await call("/cancel"); ended = true;
  byId("status").textContent = "Session cancelled. No knowledge was accepted or written.";
}));

perform(async () => {
  if (window.top !== window.self || !window.isSecureContext || !navigator.credentials || !/^[A-Za-z0-9_-]{43}$/.test(token)) throw new Error("Use the operator's localhost capability URL in a top-level browser window.");
  const session = await call("/session");
  showReview(session.review);
  byId("status").textContent = "Read the proposal, then register a credential for this temporary demo.";
});

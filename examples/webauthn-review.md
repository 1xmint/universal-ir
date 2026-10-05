# Exercise a prepared review assertion

This is a working **fictional software-authenticator demonstration** of the [internal WebAuthn component](../docs/specs/webauthn-review-v1.md). It creates a temporary project and ephemeral P-256 key, builds a real signed assertion, verifies it against an exact prepared review, and rejects that assertion after source changes. No developer or device authenticates; scripted flags do not prove consent. It performs no model calls or accepted knowledge writes.

## Run it

From the Universal IR checkout, install the optional hashed dependencies in the development environment:

~~~powershell
.venv\Scripts\python -m pip install --require-hashes --only-binary=:all: -r requirements-webauthn.txt
.venv\Scripts\python -B scripts/demo_webauthn_review.py
.venv\Scripts\python -m unittest discover -s tests -p test_webauthn_review.py -v
~~~

On macOS/Linux, use `.venv/bin/python` in place of `.venv\Scripts\python`. Python 3.12+ and Git are required for current preparation. The demonstration needs no browser, passkey enrollment, paid model access, Git repository, or server. The dependency installation can use network access; the demonstration itself does not.

Expected output includes:

~~~json
{
  "status": "ok",
  "verification": "verified_under_host_configured_credential",
  "source_change_rejected": "stale_preparation",
  "verification_preserved_files": true,
  "real_user_demonstrated": false,
  "enrollment_demonstrated": false,
  "browser_ceremony_demonstrated": false,
  "acceptance": "not_established",
  "model_calls": 0
}
~~~

The actual report also includes the preparation identity. Temporary fixture files are removed when the demonstration finishes; your own project is never selected. The private test key exists only in memory and is never written or printed. Do not use the test credential or its fictional actor mapping in a real host.

## How this fits a developer's workflow

A future coding-subscription or API host could let the agent propose a requirement and use the existing CLI to prepare it. A protected review host would independently select that exact preparation, show the complete proposed requirement and effects to the developer, and request an assertion using an already authenticated credential. This component would then check the assertion against the host-fixed review and current source.

The existing coding agent still owns its model conversation and budget. Its model tools must not enroll arbitrary credentials, choose the approver, alter the review pin, administer the host, or access signing keys. A separate local reviewer is the first candidate integration; this repository does not yet provide its server, browser UI, enrollment, sessions, or operating-system restrictions. An unrestricted same-user shell can defeat an unprotected host.

A successful assertion check would be one input to future authenticated event capture and serialized acceptance. It does not turn the requirement into accepted intent, issue a host receipt, consume an event, or permit project writes. Reusing the same assertion is explicitly not prevented by this read-only component. The [acceptance protocol model](acceptance-protocol.md) describes the remaining event/publication boundary.

The next useful demonstration is a protected host showing a real review and collecting a real browser/authenticator ceremony with trusted enrollment. Only that can address the human-event gap. No task-performance or token savings have been measured for this component.

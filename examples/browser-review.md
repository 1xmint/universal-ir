# Try a temporary browser review

The [development host](../docs/specs/browser-review-demo-v1.md) connects credential registration and exact-review assertion checks to a browser. This is a source-run demonstration for a developer operating the host, not a released isolated approval service. It does not write knowledge, issue receipts, or establish accepted intent. An unrestricted local agent can defeat its enrollment/configuration boundary.

## Prepare independently selected inputs

Install the [optional hashed requirements](../requirements-webauthn.txt) in the existing Python development environment. Use Python 3.12+ and Git. Node 22 is needed only for frontend tests, not for running the host/page.

Select a project with a configured project identity and a valid external developer-statement candidate. The [preparation walkthrough](knowledge-preparation.md) defines the record and evidence/history checks. Independently select the host, actor, event, and preparation being reviewed; the candidate's entire origin must match those selections. An AI claim that it has approval is insufficient.

~~~powershell
.venv\Scripts\python -m pip install --require-hashes --only-binary=:all: -r requirements-webauthn.txt
.venv\Scripts\python -B -m universal_ir prepare-knowledge C:\path\to\project C:\outside\candidate.json
~~~

Use the returned preparation identity only after independently reviewing the selected inputs. Start the temporary host from the Universal IR checkout:

~~~powershell
.venv\Scripts\python -B scripts/browser_review_demo.py --root C:\path\to\project --candidate-path C:\outside\candidate.json --preparation-id sha256:<reviewed-digest> --project-id your-project --host-id your-host --actor-id your-actor --event-id your-event
~~~

Replace every placeholder; do not type the angle brackets literally. On macOS/Linux, use `.venv/bin/python` and corresponding paths. This command is a development adapter, not a stable public CLI. The project is read-only throughout.

## Review in the browser

The operator opens the printed localhost capability URL in a top-level browser with WebAuthn support. Keep that URL private; do not give it to model tools. The browser removes its fragment from displayed history, so a reload requires reopening the original URL. The capability expires after ten minutes, while each credential request lasts two minutes.

1. Read the exact proposed statement, scope, identity, evidence/history summary, and complete expandable review. Unknown semantics and unverified attribution remain visible.
2. Choose **Register a temporary credential** and perform the browser/authenticator prompt yourself. Registration requests ES256 and no device attestation. No credential is stored by Universal IR after the session; your authenticator/password manager may retain the created credential under `localhost`.
3. Choose **Prepare this review for approval**. Read the exact current review and request expiry, then acknowledge the statement, scope, evidence, and transition.
4. Choose **Authenticate this exact review** and perform the assertion prompt yourself. Success returns the existing read-only verification result and closes the session. It still reports no accepted intent or writes.
5. Use **Cancel this session** or Ctrl+C to stop. Restart against a newly reviewed preparation after source changes; the host never silently updates the review pin.

If a credential prompt is cancelled/unavailable, restart that step. If the profile, expiry, or source checks fail, no approval is accepted. This narrow prototype may reject real devices with unsupported algorithms, attestation formats, or extensions. Do not automate a real credential creation or treat successful software tests as a real developer event.

## Check the implementation

~~~powershell
.venv\Scripts\python -m unittest discover -s tests -p test_browser_review.py -v
node --test tests/browser_review.test.cjs
~~~

The Python suite uses fictional software credentials and actual loopback transport. The Node suite runs frontend conversion, acknowledgement, safe text rendering, cancellation, and stale-result behavior with a scripted transport. These checks and visual browser inspection do not demonstrate a real person or device. No such real ceremony was performed for this increment.

The next gate is a protected host with authenticated operator enrollment, explicit restrictions on agent capabilities, and a real developer/browser/authenticator demonstration. Receipt/event persistence and serialized acceptance must follow before conversational requirements can be written. No paid model call, remote deployment, or performance claim is involved.

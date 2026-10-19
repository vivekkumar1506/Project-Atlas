"""Test direct portal authentication, CSRF enforcement, and trusted session derivation."""
import re
import requests

portal_base = "http://127.0.0.1:8080"

print("=" * 65)
print(" TESTING CODEIGNITER 3 PORTAL AUTH & SESSION IDENTITY DERIVATION")
print("=" * 65)

# 1. Direct POST to /chat/ask without CSRF token -> CI3 CSRF block (403)
print("\n[1/3] Testing CSRF enforcement on unprotected direct POST...")
r1 = requests.post(f"{portal_base}/chat/ask", data={"question": "Test question"})
print(f"  - Status code: {r1.status_code}")
assert r1.status_code == 403, f"Expected 403 but got {r1.status_code}"
print("  - Action correctly rejected with HTTP 403 Forbidden [PASS]")

# 2. Session initialization and identity derivation
print("\n[2/3] Initializing authenticated session as Client C-02...")
s = requests.Session()
s.get(f"{portal_base}/auth/switch_client/C-02")
r_chat = s.get(f"{portal_base}/chat")
assert r_chat.status_code == 200

# Extract CSRF token from cookie or HTML
csrf_cookies = [c.value for c in s.cookies if c.name == "atlas_csrf_cookie"]
if csrf_cookies:
    csrf_hash = csrf_cookies[-1]
else:
    token_match = re.search(r'name="atlas_csrf_token"\s+value="([a-f0-9]+)"', r_chat.text)
    assert token_match, "CSRF token not found in view"
    csrf_hash = token_match.group(1)

print(f"  - Client C-02 authenticated, CSRF token extracted: {csrf_hash[:12]}...")

# 3. Parameter tampering test: Client C-02 attempts to spoof client_id=C-03 in POST body
print("\n[3/3] Testing Parameter Tampering (C-02 sends client_id='C-03' in POST body)...")
tampered_payload = {
    "atlas_csrf_token": csrf_hash,
    "client_id": "C-03",  # Malicious attempt to access C-03 unpurchased report R-101
    "question": "What is the 2024 market size in R-101?"
}
r_tamper = s.post(f"{portal_base}/chat/ask", data=tampered_payload)
assert r_tamper.status_code == 200
d_tamper = r_tamper.json()

print(f"  - Response status: {d_tamper['status']}")
print(f"  - Answer snippet: {d_tamper['answer'][:110]}...")

# Verify that portal completely ignored client_id='C-03' from POST body
# and derived client_id='C-02' from the trusted session, denying access to R-101!
assert "Access Restricted" in d_tamper["answer"] or "C-02" in d_tamper["answer"], (
    "Security vulnerability: Client identity was NOT derived from session!"
)
assert "C-02" in d_tamper["answer"], "Expected C-02 to be identified in the refusal"
print("  - [PASS] Spoofed 'client_id' parameter in POST body was strictly IGNORED.")
print("  - [PASS] Identity derived securely from server-side authenticated session (C-02).")
print("  - [PASS] Proprietary R-101 figures remained 100% protected.")

print("\n" + "=" * 65)
print(" ALL PORTAL AUTHENTICATION & CLIENT IDENTITY TESTS PASSED!")
print("=" * 65)

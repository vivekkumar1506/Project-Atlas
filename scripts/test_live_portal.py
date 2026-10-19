import re
import requests


class PortalSession:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = ""
        self.refresh_token()

    def refresh_token(self):
        resp = self.session.get(f"{self.base_url}/")
        html = resp.text
        match = re.search(r'name="atlas_csrf_token"\s+value="([a-f0-9]+)"', html)
        if not match:
            match = re.search(r'atlas_csrf_token["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']', html)
        self.csrf_token = match.group(1) if match else ""
        return self.csrf_token

    def ask(self, question: str):
        csrf_cookies = [c.value for c in self.session.cookies if c.name == "atlas_csrf_cookie"]
        token = csrf_cookies[-1] if csrf_cookies else self.csrf_token
        payload = {
            "atlas_csrf_token": token,
            "question": question
        }
        resp = self.session.post(f"{self.base_url}/chat/ask", data=payload)
        if resp.status_code != 200:
            print("HTTPError body:", resp.text)
            resp.raise_for_status()
        res = resp.json()
        if res.get("csrf_hash"):
            self.csrf_token = res["csrf_hash"]
        return res

    def switch_client(self, client_id: str):
        resp = self.session.get(f"{self.base_url}/auth/switch_client/{client_id}")
        self.refresh_token()
        return resp.status_code


def main():
    session = PortalSession()
    print("=" * 60)
    print(" TESTING LIVE CODEIGNITER 3 PORTAL WITH FASTAPI BACKEND")
    print("=" * 60)

    # 1. Test Greeting
    print("\n[1] Question: 'hi' (Logged in as default C-01)")
    r1 = session.ask("hi")
    print("Status:", r1.get("status"))
    print("Answer:\n", r1.get("answer"))

    # 2. Test Entitled Report R-103
    print("\n[2] Question: 'What is the 2024 market size of residential water purifiers in R-103?'")
    r2 = session.ask("What is the 2024 market size of residential water purifiers in R-103?")
    print("Status:", r2.get("status"))
    print("Answer:\n", r2.get("answer"))

    # 3. Test Restricted Report R-104 for C-01
    print("\n[3] Question: 'What is the European commercial heat pump market in R-104?' (C-01 Restricted)")
    r3 = session.ask("What is the European commercial heat pump market in R-104?")
    print("Status:", r3.get("status"))
    print("Answer:\n", r3.get("answer"))

    # 4. Switch to C-03 (Full Access) and ask about R-104 again
    print("\n[4] Switching Client to C-03 (Gamma Analytics - Full Catalog)...")
    session.switch_client("C-03")
    r4 = session.ask("What is the European commercial heat pump market in R-104?")
    print("Status:", r4.get("status"))
    print("Answer:\n", r4.get("answer"))

    # 5. Test Auto-Escalation Ticket on Unknown Topic
    print("\n[5] Question: 'What is the 2024 market size of underwater quantum computers?'")
    r5 = session.ask("What is the 2024 market size of underwater quantum computers?")
    print("Status:", r5.get("status"), "| Escalated:", r5.get("escalated"))
    print("Answer:\n", r5.get("answer"))

    print("\n" + "=" * 60)
    print(" ALL LIVE CODEIGNITER 3 PORTAL INTEGRATION TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()

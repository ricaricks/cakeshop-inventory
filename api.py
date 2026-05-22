import requests
from config import BASE_URL


class ApiClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def login(self, email, password):
        r = self.session.post(f"{BASE_URL}/auth/login",
                              json={"email": email, "password": password}, timeout=8)
        data = r.json()
        token = (data.get("data") or {}).get("accessToken") or data.get("accessToken")
        if token:
            self.token = token
            self.session.headers["Authorization"] = f"Bearer {token}"
            return True, "OK"
        return False, data.get("message", "Login failed")

    def get(self, path, params=None):
        r = self.session.get(f"{BASE_URL}{path}", params=params, timeout=8)
        return r.json()

    def post(self, path, body):
        r = self.session.post(f"{BASE_URL}{path}", json=body, timeout=8)
        return r.json()

    def put(self, path, body):
        r = self.session.put(f"{BASE_URL}{path}", json=body, timeout=8)
        return r.json()

    def patch(self, path, body):
        r = self.session.patch(f"{BASE_URL}{path}", json=body, timeout=8)
        return r.json()


#nigga
    def delete(self, path):
        r = self.session.delete(f"{BASE_URL}{path}", timeout=8)
        return r.json() if r.content else {"success": r.status_code < 300}
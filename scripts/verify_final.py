import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=== Test Auth ===")
print("v1 login:", client.post("/api/v1/auth/login", json={"username":"admin","password":"admin123"}).status_code)
print("legacy login:", client.post("/auth/login", json={"username":"admin","password":"admin123"}).status_code)

print("\n=== Test Routes ===")
admin_response = client.post("/auth/login", json={"username":"admin","password":"admin123"})
if admin_response.status_code == 200:
    admin_token = admin_response.json()["access_token"]
    print("v1 absensi:", client.get("/api/v1/absensi/", headers={"Authorization": f"Bearer {admin_token}"}).status_code)
    print("legacy absensi:", client.get("/absensi/", headers={"Authorization": f"Bearer {admin_token}"}).status_code)

print("\n=== Test API Docs ===")
print("OpenAPI paths:", len(client.get("/openapi.json").json()["paths"]))

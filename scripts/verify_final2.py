import sqlite3
from fastapi.testclient import TestClient

print("=== DATABASE VERIFICATION ===")
con = sqlite3.connect('db_absensi.db')
cur = con.cursor()

print("Kelas:", cur.execute('SELECT * FROM kelas').fetchall())
print("Users:", cur.execute('SELECT id, username, nim, role FROM users').fetchall())
print("Mahasiswa:", cur.execute('SELECT nim, nama_lengkap, kelas_id FROM mahasiswa').fetchall())
print("Absensi count:", cur.execute('SELECT COUNT(*) FROM absensi').fetchone()[0])

print("\n=== TESTING API ROUTES ===")
from main import app
client = TestClient(app)

print("v1 /api/v1/auth/login:", client.post("/api/v1/auth/login", json={"username":"admin","password":"admin123"}).status_code)
print("legacy /auth/login:", client.post("/auth/login", json={"username":"admin","password":"admin123"}).status_code)

admin_response = client.post("/auth/login", json={"username":"admin","password":"admin123"})
if admin_response.status_code == 200:
    admin_token = admin_response.json()["access_token"]
    print("\nv1 /api/v1/absensi/:", client.get("/api/v1/absensi/", headers={"Authorization": f"Bearer {admin_token}"}).status_code)
    print("legacy /absensi/:", client.get("/absensi/", headers={"Authorization": f"Bearer {admin_token}"}).status_code)

print("\n=== OpenAPI ===")
print("Paths:", len(client.get("/openapi.json").json()["paths"]))
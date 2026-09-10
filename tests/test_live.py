import urllib.request
import json

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    # 1. Health check
    res = urllib.request.urlopen(f"{BASE_URL}/api/health")
    data = json.loads(res.read())
    print(f"[LIVE TEST] Health: {data['status']}, Total parcels: {data['total_parcels']}")
    assert data["status"] == "ONLINE"

    # 2. Login
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": "APCRDA_OFFICER", "role": "OFFICIAL"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    login_data = json.loads(res.read())
    print(f"[LIVE TEST] Auth Login: {login_data['status']}, Role: {login_data['user']['role']}")
    assert login_data["status"] == "SUCCESS"
    assert login_data["user"]["role"] == "OFFICIAL"

    # 3. Topology Check
    req = urllib.request.Request(
        f"{BASE_URL}/api/topology/check",
        data=json.dumps({"center_x": 0, "center_y": 0, "width": 14, "length": 14, "z_min": 0, "z_max": 28.8}).encode(),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    topo_data = json.loads(res.read())
    print(f"[LIVE TEST] Topology Check: {topo_data['status']}, Conflicts found: {topo_data['validation']['conflict_count']}")
    assert topo_data["status"] == "SUCCESS"

    # 4. Generate 3D ULPIN
    import time
    ts = int(time.time())
    req = urllib.request.Request(
        f"{BASE_URL}/api/ulpin/generate",
        data=json.dumps({
            "base_ulpin": f"28GNT{ts % 10000000000:010d}",
            "zone_type": "FLR",
            "z_min": 100.0 + (ts % 50),
            "z_max": 103.2 + (ts % 50),
            "floor_number": 25,
            "unit_code": "2501",
            "center_x": 1000.0 + (ts % 200),
            "center_y": 1000.0 + (ts % 200),
            "width": 10.0,
            "length": 10.0,
            "owner": "Sri Sai Nilayam",
            "tenure_type": "Freehold 3D Strata"
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    gen_data = json.loads(res.read())
    print(f"[LIVE TEST] 3D ULPIN Issue: {gen_data['status']}, ULPIN: {gen_data['parcel']['ulpin_3d']}")
    assert gen_data["status"] == "SUCCESS"

    print("\nALL LIVE REST API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()

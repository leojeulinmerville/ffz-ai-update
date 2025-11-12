def test_register_duplicate(client):
    payload = {"email": "duplicate@example.com", "password": "Passw0rd!", "language": "en"}
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200

    resp_dup = client.post("/auth/register", json=payload)
    assert resp_dup.status_code == 409
    assert resp_dup.json()["detail"] == "Email already registered"

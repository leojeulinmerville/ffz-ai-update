def test_register_login_and_subscribe(client):
    # Register
    r = client.post("/auth/register", json={"email":"t@t.com","password":"pass1234","language":"fr"})
    assert r.status_code == 200

    # Login
    r = client.post("/auth/login", json={"email":"t@t.com","password":"pass1234"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Empty subs
    r = client.get("/subscriptions", headers=headers)
    assert r.status_code == 200
    assert r.json() == []

    # Add sub
    payload = {"league":"FRA1","team":"PSG","frequency":"weekly"}
    r = client.post("/subscriptions", headers=headers, json=payload)
    assert r.status_code == 200
    sub_id = r.json()["id"]

    # List again
    r = client.get("/subscriptions", headers=headers)
    assert any(s["id"] == sub_id for s in r.json())

    # Delete
    r = client.delete(f"/subscriptions/{sub_id}", headers=headers)
    assert r.status_code == 200

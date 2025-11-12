from app.services.whatsapp_sender import normalize_fr_phone

def test_admin_register_and_follow(client):
    register_payload = {
        "email": "adminflow@test.com",
        "password": "pass1234",
        "language": "en",
        "phone_number": "0600000000",
    }

    resp = client.post("/auth/register", json=register_payload)
    assert resp.status_code == 200

    login = client.post("/auth/login", json={"email": register_payload["email"], "password": register_payload["password"]})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    leagues_resp = client.get("/meta/leagues")
    assert leagues_resp.status_code == 200
    leagues = leagues_resp.json().get("leagues", [])
    assert len(leagues) >= 1

    first_code = leagues[0]["code"]
    teams_resp = client.get(f"/meta/leagues/{first_code}/teams")
    assert teams_resp.status_code == 200

    follow_resp = client.post("/subscriptions/bulk", headers=headers, json={"leagues": [first_code]})
    assert follow_resp.status_code == 200
    assert first_code in follow_resp.json().get("created", [])

    subs_resp = client.get("/subscriptions", headers=headers)
    assert any(sub["league"] == first_code for sub in subs_resp.json())

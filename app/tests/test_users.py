TEST_USER_DATA = {
    "username": "admin",
    "email": "admin@admin.com",
    "first_name": None,
    "last_name": None,
    "password": "admin",
}


def test_create_user(client):
    response = client.post("/users/register", data=TEST_USER_DATA)
    assert response.status_code == 201


def test_get_token(add_user, client):
    response = client.post("/users/token", data=TEST_USER_DATA)
    assert response.status_code == 200


def test_get_user_by_username(add_user, client):
    response = client.get(f"/users/{TEST_USER_DATA['username']}")
    assert response.status_code == 200


def test_login(add_user, user_token, client):
    response = client.get("/users/logined_user", headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200

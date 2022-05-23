TEST_USER_DATA = {
    "username": "admin",
    "email": "admin@admin.com",
    "first_name": None,
    "last_name": None,
    "password": "admin",
}

TEST_FILE_PATH = 'files_to_upload'


def test_upload_file(add_user, user_token, client):
    with open(f'{TEST_FILE_PATH}/simple_file.txt', 'rb') as file:
        response = client.post("/files/upload",
                               headers={'Authorization': f'Bearer {user_token}'},
                               files=[('file', file)])
    assert response.status_code == 200


def test_upload_large_file(add_user, user_token, client):
    with open(f'{TEST_FILE_PATH}/large_file.txt', 'rb') as file:
        response = client.post("/files/upload",
                               headers={'Authorization': f'Bearer {user_token}'},
                               files=[('file', file)])
    assert response.status_code == 422
    assert 'Your file too big' in response.json()['detail']


def test_upload_same_file(add_user, user_token, add_simple_file, client):
    with open(f'{TEST_FILE_PATH}/simple_file_copy.txt', 'rb') as file:
        response = client.post("/files/upload",
                               headers={'Authorization': f'Bearer {user_token}'},
                               files=[('file', file)])
    assert response.status_code == 400
    assert response.json()['detail'] == 'You already have File with same content'


def test_get_user_files(add_user, user_token, add_simple_file, client):
    response = client.get("/files/", headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    assert 'simple_file.txt' in response.json()


def test_delete_file(add_user, user_token, add_simple_file, client):
    response = client.delete(f"/files/simple_file.txt", headers={'Authorization': f'Bearer {user_token}'})
    assert response.status_code == 200
    assert 'successfully deleted' in response.json()

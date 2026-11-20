def calculate_study_duration(start_minutes, end_minutes):
    return end_minutes - start_minutes


def test_calculate_study_duration():
    result = calculate_study_duration(30, 90)

    assert result == 60


def test_register_user(client):
    response = client.post( "/register",
                           json={"username": "mosi",
                            "email": "mosi_test@example.com",
                              "password": "mosi123"} )
    print(response.json())

    assert response.status_code == 200

def test_login_user(client):
    response = client.post( "/login",
                            data={  "username": "admin_test",
                                 "password": "testpassword123"})

    assert response.status_code == 200


def test_create_course(client):

        response = client.post("/login",
                               data={"username": "admin_test",
                                 "password": "testpassword123"})
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post( "/courses",
                            json={"title": "Test Course2",
                                  "description": "Test Description2",
                                  "level": "basic"},
                            headers=headers)
        print(response.json())
        assert response.status_code == 200


def test_read_courses(client):
    response = client.get("/courses")
    print(response.json())
    assert response.status_code == 200

def test_read_course(client):
    response = client.get("/courses/1")
    print(response.json())
    assert response.status_code == 200


def test_update_course(client):
    response = client.post("/login",
                data = { "username": "admin_test","password": "testpassword123" })

    assert response.status_code == 200

    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    response = client.patch("/courses/1/course",
                            json={"title": "Test Course",
                                  "description": "Test Description",
                                  "level": "basic"},
                            headers=headers)
    print(response.json())
    assert response.status_code == 200



def test_delete_course(client):
    response = client.post("/login",
                           data = { "username": "admin_test","password": "testpassword123" })
    assert response.status_code == 200

    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/courses/1",headers=headers )
    print(response.json())
    assert response.status_code == 200


def test_assigning_a_lesson_to_course(client):
    response = client.post("/login",
                           data = { "username": "admin_test","password": "testpassword123" })
    assert response.status_code == 200

    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/courses/2/lessons",
                           json={"title": "Test lesson title","description": "Test lesson description",
                                 "content":"test lesson content","order":2,
                                 "course_id":2},headers=headers )
    print(response.json())
    assert response.status_code == 200

def test_removing_a_lesson_from_course(client):
    response = client.post("/login",
                           data = { "username": "admin_test","password": "testpassword123" })
    
    assert response.status_code == 200
    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/courses/2/lessons/1",headers=headers )
    print(response.json())
    assert response.status_code == 200


def test_user_get_lessons(client):
    response = client.post("/login",
                           data={"username": "admin_test","password": "testpassword123" })
    
    assert response.status_code == 200
    token = response.json()['access_token']
    headers = {"Authorization" : f"Bearer {token}"}

    response = client.get("/users/10/lessons",headers=headers )
    print(response.json())
    assert response.status_code == 200

def test_user_get_one_lesson(client):
    response = client.post("/login",
                           data = { "username": "admin_test","password": "testpassword123" })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/lessons/2",headers=headers )
    print(response.json())
    assert response.status_code == 200


def test_admin_update_lesson(client):
    response = client.post("/login",
                           data = { "username": "admin_test","password": "testpassword123" })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.patch("/lessons/2/lesson",
                            json={"title": "Test lesson title2","description": "Test lesson description2","content":"test lesson content2",
                                  "order":3},
                            headers=headers)
    print(response.json())
    assert response.status_code == 200


def test_admin_delete_lesson(client):
    response = client.post("/login",
                           data={"username": "admin_test","password": "testpassword123" })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/lessons/2",headers=headers )

    print(response.json())
    assert response.status_code == 200


def test_admin_remove_a_lesson_from_a_course(client):
    response = client.post("/login",
                          data = { "username": "admin_test","password": "testpassword12" })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post("/lessons/1/1",headers=headers )
    print(response.json())
    assert response.status_code == 200

def test_admin_assign_profile_to_user(client):
    response = client.post("/login",
                           data = { "username": "admin_test","password": "testpassword123" })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/users/4/profile",
                           json={"first_name": "testname4","last_name": "test4","bio": "test4","avatar_url":None,
                                 "native_language":"en4","learning_level":"basic4"},headers=headers)
    print(response.json())
    assert response.status_code == 200




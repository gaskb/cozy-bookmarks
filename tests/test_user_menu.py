def test_user_menu_shows_email_theme_import_and_logout(authed_client, user):
    response = authed_client.get("/")

    assert 'class="user-menu"' in response.text
    assert f'<p class="user-menu-email">{user.email}</p>' in response.text
    assert 'id="theme-select"' in response.text
    assert 'href="/bookmarks/import"' in response.text
    assert 'action="/logout"' in response.text


def test_user_menu_absent_when_logged_out(client):
    response = client.get("/login")

    assert 'class="user-menu"' not in response.text
    assert 'class="theme-switcher-inline"' in response.text
    assert 'id="theme-select"' in response.text


def test_user_menu_present_on_organize_and_import_pages_too(authed_client):
    created = authed_client.post("/bookmarks", json={"url": "https://example.com"}).json()

    organize_response = authed_client.get(f"/bookmarks/{created['id']}/organize")
    import_response = authed_client.get("/bookmarks/import")

    assert 'class="user-menu"' in organize_response.text
    assert 'class="user-menu"' in import_response.text


def test_only_one_theme_select_per_page(authed_client):
    response = authed_client.get("/")

    assert response.text.count('id="theme-select"') == 1

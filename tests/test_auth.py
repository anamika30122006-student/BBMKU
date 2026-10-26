import pytest
from app.models.user import User


def test_login_successful(client):
    res = client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Executive Dashboard' in res.data
    assert b'System Administrator' in res.data


def test_login_invalid_password(client):
    res = client.post('/auth/login', data={'username': 'admin', 'password': 'WrongPassword'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Invalid username/email or password' in res.data


def test_logout(client):
    client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    res = client.get('/auth/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'signed out' in res.data


def test_unauthorized_redirect(client):
    res = client.get('/dashboard', follow_redirects=False)
    assert res.status_code == 302
    assert '/auth/login' in res.headers['Location']

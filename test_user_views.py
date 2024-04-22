import os
from unittest import TestCase
from flask import g
from models import db, connect_db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for User."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser2 = User.signup(username="testuser2",
                                     email="tester@tester.com",
                                     password="hashed",
                                     image_url=None
        )

        self.testuser.following.append(self.testuser2)
        self.testuser2.following.append(self.testuser)
        db.session.commit()

        self.testid = self.testuser.id
        self.testid2 = self.testuser2.id

    
    def test_signup(self):
        """Tests if signup route works as expected"""
        data1 = {
            'username': 'TESTSIGNUP',
            'email': 'signup@tester.com',
            'password': 'hashed',
            'image_url' : None
        }
        resp = self.client.post('/signup', data=data1, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('@TESTSIGNUP', html)

    
    def test_invalid_signup(self):
        """Tests that signup is invalid when username taken"""

        data2 = {
            'username': 'testuser',
            'email': 'test@tester.com',
            'password': 'hashed',
            'image_url' : None
        }
        resp = self.client.post('/signup', data=data2)
        
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Username taken—please pick another", html)


    def test_login(self):
        """Tests login route works with valid credentials"""

        resp = self.client.post('/login', data={'username':'testuser',
                                                'password':'testuser',}, 
                                                follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, testuser!", html)

    def test_invalid_login(self):
        """Tests login route works with invalid credentials"""
        
        resp = self.client.post('/login', data={'username':'testuser',
                                                'password':'testuserrrrr',}, 
                                                follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Invalid credentials", html)

    def test_logout(self):
        """Tests logout route works as expected"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/logout', follow_redirects=True)

            html = resp.get_data(as_text=True)
        
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Logged out", html)


    def test_search_user(self):
        """Tests searched users are listed when logged in """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            params={'q': 'test'}
            resp = c.get('/users', query_string=params)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)


    def test_edit_user(self):
        """Tests editing user with valid password"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {'username': "testuser",
                    'email': "test@test.com",
                    'image_url': None,
                    'header_image_url': 'testheaderimage.com',
                    'bio': 'I am just a test user :)',
                    'password': "testuser"}
            
            resp=c.post('/users/profile', data = data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("profile was edited", html)
            self.assertIn('I am just a test user :)', html)


    def test_delete_user(self):
        """Tests post request route when users are deleted"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp=c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Account deleted', html)


    def test_view_followers(self):
        """Tests that user can see another user's follower page"""

        #not logged in
        invalid_resp = self.client.get(f'/users/{self.testid2}/followers', follow_redirects=True)
        self.assertEqual(invalid_resp.status_code, 200)
        self.assertIn('Access unauthorized.', invalid_resp.get_data(as_text=True))

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testid2}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)


    def test_view_following(self):
        """Tests that user can see another user's following page"""

        #not logged in
        invalid_resp = self.client.get(f'/users/{self.testid2}/following', follow_redirects=True)
        self.assertEqual(invalid_resp.status_code, 200)
        self.assertIn('Access unauthorized.', invalid_resp.get_data(as_text=True))

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/{self.testid2}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)


    def test_follow_routes(self):
        """Tests post request route to unfollow/follow another user"""

        #unfollow user
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/stop-following/{self.testid2}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@testuser2', html)

        #refollow user
            resp = c.post(f'/users/follow/{self.testid2}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser2', html)
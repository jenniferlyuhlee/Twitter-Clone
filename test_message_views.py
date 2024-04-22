"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

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

        self.testmessage = Message(text="Test Message")
        self.testuser.messages.append(self.testmessage)
        db.session.commit()

        self.messageid = self.testmessage.id

    def test_add_message_loggedin(self):
        """Tests if user can add a message when logged in"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter_by(text='Hello').first()
            self.assertEqual(msg.text, "Hello")


    def test_add_message_loggedout(self):
        """Tests that message cannot be added when logged out (no g.user)"""
        
        resp = self.client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)


    def test_delete_message_loggedin(self):
        """Tests if user can delete a message when logged in"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            #create message and save to variable to refer to id in delete route
            resp = c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.filter_by(text='Hello').first()

            #delete message
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("Hello", html)


    def test_delete_message_loggedout(self):
        """Tests that message cannot be deleted when logged out (no g.user)"""

        #delete message
        delete_resp = self.client.post(f"/messages/{self.messageid}/delete", follow_redirects=True)
        html = delete_resp.get_data(as_text=True)

        self.assertEqual(delete_resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)


    def test_like_unlike_message(self):
        """Tests route for liking/unliking message when logged in"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            #test liking
            resp = self.client.post(f"/users/add_like/{self.messageid}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            #tests that liked message displays on user likes page
            get_resp = self.client.get(f"/users/{self.testuser2.id}/likes")
            html = get_resp.get_data(as_text=True)
            self.assertIn("Test Message", html)

            #test unliking
            resp = self.client.post(f"/users/add_like/{self.messageid}", follow_redirects=True)

            #tests message does not display on user likes page anymore
            get_resp = self.client.get(f"/users/{self.testuser2.id}/likes")
            html = get_resp.get_data(as_text=True)
            self.assertNotIn("Test Message", html)

    def test_like_message_loggedout(self):
        """Tests that message cannot be liked when logged out (no g.user)"""
        
        resp = self.client.post(f"/users/add_like/{self.messageid}", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)
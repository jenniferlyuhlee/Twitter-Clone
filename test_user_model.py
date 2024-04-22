"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test User Model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        test_user1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        test_user2 = User(
            email="tester@tester.com",
            username="testuser2",
            password="hashed"
        )

        db.session.add(test_user1, test_user2)
        db.session.commit()

        self.test_user1 = test_user1
        self.test_user2 = test_user2

        self.client = app.test_client()

    def test_user_model(self):
        """Basic tests on User model"""

        # User should have no messages & no followers
        self.assertEqual(len(self.test_user1.messages), 0)
        self.assertEqual(len(self.test_user1.followers), 0)

    def test_user_messages(self):
        """Tests User - message relationship"""

        new_message = Message(text='hi')
        self.test_user1.messages.append(new_message)
        db.session.commit()
        self.assertEqual(len(self.test_user1.messages), 1)

    def test_repr(self):
        """Tests if repr method works as expected"""
        
        self.assertEqual(self.test_user1.__repr__(), 
                         f"<User #{self.test_user1.id}: testuser, test@test.com>")
        
    def test_follows(self):
        """
        Tests if is_following/is_followed_by successfully detects follow relationships:
            when user1 is (not) following user2
            when user2 is (not) followed by user1
        """

        self.test_user1.following.append(self.test_user2)
        db.session.commit()

        self.assertTrue(self.test_user1.is_following(self.test_user2))
        self.assertEqual(len(self.test_user1.following), 1)
        self.assertTrue(self.test_user2.is_followed_by(self.test_user1))
        self.assertEqual(len(self.test_user2.followers), 1)

        self.test_user1.following.remove(self.test_user2)
        db.session.commit()

        self.assertFalse(self.test_user1.is_following(self.test_user2))
        self.assertEqual(len(self.test_user1.following), 0)
        self.assertFalse(self.test_user2.is_followed_by(self.test_user1))
        self.assertEqual(len(self.test_user2.followers), 0)

    def test_signup(self):
        """Tests User class method signup with valid/invalid credentials"""

        new_testuser = User.signup(
                username='newtester',
                password='testpw',
                email='testemail@email.com',
                image_url='testimage.com')
        
        db.session.commit()
        self.assertIsInstance(new_testuser, User)
        self.assertEqual(new_testuser.username, 'newtester')
        self.assertEqual(new_testuser.email, 'testemail@email.com')
    
        # self.assertRaises(IntegrityError,
        #     User.signup, username=None,
        #                 password='testpw',
        #                 email='testingemail@email.com',
        #                 image_url='testimage.com')
    
 
    def test_authentication(self):
        """Tests User class method authentication
        Returns user if authenticated
        Else returns False
        """

        #need to have User instance made through signup to hash password correctly
        new_testuser = User.signup(
                username='newtester',
                password='testpw',
                email='testemail@email.com',
                image_url='testimage.com')
        
        self.assertIs(User.authenticate('newtester', 'testpw'), 
                      new_testuser)
        self.assertFalse(User.authenticate('wrongusername', 'HASHED_PASSWORD'), 
                      new_testuser)
        self.assertFalse(User.authenticate('testuser', 'wrongpassword'), 
                      new_testuser)
        


    


        

        


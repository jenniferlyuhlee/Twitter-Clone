import os
from unittest import TestCase

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class MessageModelTestCase(TestCase):
    """Test Message Model"""

    def setUp(self):
        """Create test client and sample data"""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        test_user1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        new_msg = Message(text='Test message!')
        another_msg = Message(text='TESTING!!!')

        db.session.add(test_user1)
        test_user1.messages.extend([new_msg, another_msg])
        db.session.commit()

        self.test_user1 = test_user1
        self.new_msg = new_msg
        self.another_msg = another_msg

        self.client = app.test_client()


    def test_message_model(self):
        """Basic test on Message model"""

        self.assertEqual(self.new_msg.text, 'Test message!')
        self.assertEqual(self.another_msg.text, 'TESTING!!!')


    def test_message_user_relationship(self):
        """Tests relationship between Message and User models
        Checks if new messages are being integrated into relationship properly
        """
        
        self.assertEqual(self.new_msg.user_id, self.test_user1.id)
        self.assertEqual(self.another_msg.user_id, self.test_user1.id)
        self.assertEqual(len(self.test_user1.messages), 2)

        new_test_msg1 = Message(text='ANOTHER TEST')
        new_test_msg2 = Message(text='RELATIONSHIP')
        
        #extend instead of append to add multiple messages
        self.test_user1.messages.extend([new_test_msg1, new_test_msg2])
        db.session.commit()

        self.assertEqual(self.new_msg.user_id, self.test_user1.id)
        self.assertEqual(self.another_msg.user_id, self.test_user1.id)
        self.assertEqual(len(self.test_user1.messages), 4)


    def test_message_deletion(self):
        """Tests User-Message relationship and detection of message deletions"""

        db.session.delete(self.new_msg)
        db.session.commit()
        self.assertNotIn(self.new_msg, self.test_user1.messages)
        self.assertEqual(len(self.test_user1.messages), 1)

        db.session.delete(self.another_msg)
        db.session.commit()
        self.assertNotIn(self.another_msg, self.test_user1.messages)
        self.assertEqual(len(self.test_user1.messages), 0)

    
    def test_toggling_likes(self):
        """Tests User-Likes-Messages relationship and 
        toggling likes on messages"""

        test_user2 = User(
            email="tester@tester.com",
            username="testuser2",
            password="hashed"
        )
        db.session.add(test_user2)
        db.session.commit()

        like_msg = Message(text='Liking message', user_id = test_user2.id)

        self.test_user1.likes.append(like_msg)
        db.session.commit()
        self.assertIn(like_msg, self.test_user1.likes)

        self.test_user1.likes.remove(like_msg)
        db.session.commit()
        self.assertNotIn(like_msg, self.test_user1.likes)


    def test_likes_deletion(self):
        """Tests if message is removed from likes when deleted"""

        test_user2 = User(
            email="tester@tester.com",
            username="testuser2",
            password="hashed"
        )
        db.session.add(test_user2)
        test_user2.likes.append(self.new_msg)
        db.session.commit()

        self.assertIn(self.new_msg, test_user2.likes)

        db.session.delete(self.new_msg)
        db.session.commit()

        self.assertNotIn(self.new_msg, test_user2.likes)











from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Todo

class TodoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.todo = Todo.objects.create(
            title='Test Todo',
            description='Test Description',
            user=self.user
        )

    def test_todo_creation(self):
        self.assertEqual(self.todo.title, 'Test Todo')
        self.assertEqual(self.todo.description, 'Test Description')
        self.assertFalse(self.todo.completed)
        self.assertEqual(self.todo.user, self.user)

    def test_todo_str(self):
        self.assertEqual(str(self.todo), 'Test Todo')

class TodoViewTest(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        
        # Create todos for each user
        self.todo1 = Todo.objects.create(title='Todo 1', user=self.user1)
        self.todo2 = Todo.objects.create(title='Todo 2', user=self.user2)
        
        self.client = Client()

    def test_login_required(self):
        """Test that all views require login"""
        urls = [
            reverse('todo_list'),
            reverse('todo_create'),
            reverse('todo_update', args=[self.todo1.pk]),
            reverse('todo_delete', args=[self.todo1.pk]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(response, f'/accounts/login/?next={url}')

    def test_todo_list_shows_only_own_todos(self):
        self.client.login(username='user1', password='password')
        response = self.client.get(reverse('todo_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Todo 1')
        self.assertNotContains(response, 'Todo 2')

    def test_todo_create(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('todo_create'), {
            'title': 'New Todo',
            'description': 'New Description',
            'completed': False
        })
        self.assertRedirects(response, reverse('todo_list'))
        self.assertTrue(Todo.objects.filter(title='New Todo', user=self.user1).exists())

    def test_todo_update_own(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('todo_update', args=[self.todo1.pk]), {
            'title': 'Updated Todo 1',
            'description': '',
            'completed': True
        })
        self.assertRedirects(response, reverse('todo_list'))
        self.todo1.refresh_from_db()
        self.assertEqual(self.todo1.title, 'Updated Todo 1')
        self.assertTrue(self.todo1.completed)

    def test_todo_update_other_user(self):
        """Test that user1 cannot update user2's todo"""
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('todo_update', args=[self.todo2.pk]), {
            'title': 'Hacked Todo',
        })
        # Should return 404 because get_object_or_404 filters by user
        self.assertEqual(response.status_code, 404)
        self.todo2.refresh_from_db()
        self.assertEqual(self.todo2.title, 'Todo 2')

    def test_todo_delete_own(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('todo_delete', args=[self.todo1.pk]))
        self.assertRedirects(response, reverse('todo_list'))
        self.assertFalse(Todo.objects.filter(pk=self.todo1.pk).exists())

    def test_todo_delete_other_user(self):
        """Test that user1 cannot delete user2's todo"""
        self.client.login(username='user1', password='password')
        response = self.client.post(reverse('todo_delete', args=[self.todo2.pk]))
        # Should return 404 because get_object_or_404 filters by user
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todo.objects.filter(pk=self.todo2.pk).exists())

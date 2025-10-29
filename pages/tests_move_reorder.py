from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Employee, Board, BoardList, Card
import json


class MoveCardReorderTests(TestCase):
    def setUp(self):
        # create a user and employee profile
        self.user = User.objects.create_user(username='tester', email='tester@example.com', password='pass')
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='E001',
            position='Tester',
            phone='123',
            is_active=True,
            is_email_verified=True
        )

        self.client = Client()
        # log in the test client
        self.client.force_login(self.user)

    def test_move_within_list_reorders(self):
        board = Board.objects.create(title='Board', created_by=self.employee)
        board.members.add(self.employee)

        bl = BoardList.objects.create(title='List A', board=board, position=1)

        c1 = Card.objects.create(title='A', board_list=bl, created_by=self.employee, position=1)
        c2 = Card.objects.create(title='B', board_list=bl, created_by=self.employee, position=2)
        c3 = Card.objects.create(title='C', board_list=bl, created_by=self.employee, position=3)

        url = reverse('move_card')
        payload = {'card_id': str(c1.id), 'new_list_id': str(bl.id), 'new_position': 3}

        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)

        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        # expected order: B, C, A
        self.assertEqual(ordered, ['B', 'C', 'A'])

    def test_move_across_lists_reorders(self):
        board = Board.objects.create(title='Board2', created_by=self.employee)
        board.members.add(self.employee)

        list1 = BoardList.objects.create(title='List 1', board=board, position=1)
        list2 = BoardList.objects.create(title='List 2', board=board, position=2)

        a = Card.objects.create(title='A', board_list=list1, created_by=self.employee, position=1)
        b = Card.objects.create(title='B', board_list=list1, created_by=self.employee, position=2)

        url = reverse('move_card')
        payload = {'card_id': str(a.id), 'new_list_id': str(list2.id), 'new_position': 1}

        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)

        list1_titles = list(Card.objects.filter(board_list=list1).order_by('position').values_list('title', flat=True))
        list2_titles = list(Card.objects.filter(board_list=list2).order_by('position').values_list('title', flat=True))

        self.assertEqual(list1_titles, ['B'])
        self.assertEqual(list2_titles, ['A'])

    def test_move_to_start_within_list(self):
        board = Board.objects.create(title='Board-start', created_by=self.employee)
        board.members.add(self.employee)

        bl = BoardList.objects.create(title='List S', board=board, position=1)
        c1 = Card.objects.create(title='1', board_list=bl, created_by=self.employee, position=1)
        c2 = Card.objects.create(title='2', board_list=bl, created_by=self.employee, position=2)
        c3 = Card.objects.create(title='3', board_list=bl, created_by=self.employee, position=3)
        c4 = Card.objects.create(title='4', board_list=bl, created_by=self.employee, position=4)

        url = reverse('move_card')
        payload = {'card_id': str(c3.id), 'new_list_id': str(bl.id), 'new_position': 1}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)

        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['3', '1', '2', '4'])

    def test_move_to_end_within_list(self):
        board = Board.objects.create(title='Board-end', created_by=self.employee)
        board.members.add(self.employee)

        bl = BoardList.objects.create(title='List E', board=board, position=1)
        a = Card.objects.create(title='A', board_list=bl, created_by=self.employee, position=1)
        b = Card.objects.create(title='B', board_list=bl, created_by=self.employee, position=2)
        c = Card.objects.create(title='C', board_list=bl, created_by=self.employee, position=3)

        url = reverse('move_card')
        payload = {'card_id': str(b.id), 'new_list_id': str(bl.id), 'new_position': 999}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)

        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['A', 'C', 'B'])

    def test_move_up_and_down_adjacent(self):
        board = Board.objects.create(title='Board-adj', created_by=self.employee)
        board.members.add(self.employee)

        bl = BoardList.objects.create(title='List Adj', board=board, position=1)
        one = Card.objects.create(title='one', board_list=bl, created_by=self.employee, position=1)
        two = Card.objects.create(title='two', board_list=bl, created_by=self.employee, position=2)
        three = Card.objects.create(title='three', board_list=bl, created_by=self.employee, position=3)

        url = reverse('move_card')
        # move two down to position 3
        payload = {'card_id': str(two.id), 'new_list_id': str(bl.id), 'new_position': 3}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['one', 'three', 'two'])

        # move three up to position 2
        payload = {'card_id': str(three.id), 'new_list_id': str(bl.id), 'new_position': 2}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['one', 'three', 'two'])

    def test_noop_move_same_position(self):
        board = Board.objects.create(title='Board-noop', created_by=self.employee)
        board.members.add(self.employee)

        bl = BoardList.objects.create(title='List N', board=board, position=1)
        c1 = Card.objects.create(title='X', board_list=bl, created_by=self.employee, position=1)
        c2 = Card.objects.create(title='Y', board_list=bl, created_by=self.employee, position=2)

        url = reverse('move_card')
        payload = {'card_id': str(c1.id), 'new_list_id': str(bl.id), 'new_position': 1}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['X', 'Y'])

    def test_clamp_zero_and_negative_position(self):
        board = Board.objects.create(title='Board-clamp', created_by=self.employee)
        board.members.add(self.employee)

        bl = BoardList.objects.create(title='List C', board=board, position=1)
        c1 = Card.objects.create(title='first', board_list=bl, created_by=self.employee, position=1)
        c2 = Card.objects.create(title='second', board_list=bl, created_by=self.employee, position=2)

        url = reverse('move_card')
        payload = {'card_id': str(c2.id), 'new_list_id': str(bl.id), 'new_position': 0}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['second', 'first'])

        # negative position
        payload = {'card_id': str(c1.id), 'new_list_id': str(bl.id), 'new_position': -5}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        ordered = list(Card.objects.filter(board_list=bl).order_by('position').values_list('title', flat=True))
        self.assertEqual(ordered, ['first', 'second'])

    def test_cross_list_various_positions(self):
        board = Board.objects.create(title='Board-cross', created_by=self.employee)
        board.members.add(self.employee)

        s = BoardList.objects.create(title='Source', board=board, position=1)
        t = BoardList.objects.create(title='Target', board=board, position=2)

        a = Card.objects.create(title='a', board_list=s, created_by=self.employee, position=1)
        b = Card.objects.create(title='b', board_list=s, created_by=self.employee, position=2)
        c = Card.objects.create(title='c', board_list=t, created_by=self.employee, position=1)
        d = Card.objects.create(title='d', board_list=t, created_by=self.employee, position=2)

        url = reverse('move_card')

        # move a to target at position 1 (start)
        payload = {'card_id': str(a.id), 'new_list_id': str(t.id), 'new_position': 1}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(list(Card.objects.filter(board_list=t).order_by('position').values_list('title', flat=True)), ['a', 'c', 'd'])

        # move b to target at middle (position 2)
        payload = {'card_id': str(b.id), 'new_list_id': str(t.id), 'new_position': 2}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(list(Card.objects.filter(board_list=t).order_by('position').values_list('title', flat=True)), ['a', 'b', 'c', 'd'])

        # move c back to source at end
        payload = {'card_id': str(c.id), 'new_list_id': str(s.id), 'new_position': 999}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertTrue('c' in list(Card.objects.filter(board_list=s).order_by('position').values_list('title', flat=True)))

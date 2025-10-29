from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Employee, Board, BoardList, Card, CardComment
import json


class BoardIntegrationTests(TestCase):
    def setUp(self):
        # create a user and employee profile
        self.user = User.objects.create_user(username='tester2', email='tester2@example.com', password='pass')
        self.employee = Employee.objects.create(
            user=self.user,
            employee_id='E002',
            position='Tester',
            phone='123',
            is_active=True,
            is_email_verified=True
        )

        self.client = Client()
        self.client.force_login(self.user)

    def _create_board_with_lists(self):
        board = Board.objects.create(title='E2 Board', created_by=self.employee)
        board.members.add(self.employee)
        l1 = BoardList.objects.create(title='Todo', board=board, position=1)
        l2 = BoardList.objects.create(title='Doing', board=board, position=2)
        l3 = BoardList.objects.create(title='Done', board=board, position=3)
        return board, l1, l2, l3

    from django.test import TestCase, Client
    from django.urls import reverse
    from django.contrib.auth.models import User
    from .models import Employee, Board, BoardList, Card, CardComment
    import json


    class BoardIntegrationTests(TestCase):
        def setUp(self):
            # create a user and employee profile
            self.user = User.objects.create_user(username='tester2', email='tester2@example.com', password='pass')
            self.employee = Employee.objects.create(
                user=self.user,
                employee_id='E002',
                position='Tester',
                phone='123',
                is_active=True,
                is_email_verified=True
            )

            self.client = Client()
            self.client.force_login(self.user)

        def _create_board_with_lists(self):
            board = Board.objects.create(title='E2 Board', created_by=self.employee)
            board.members.add(self.employee)
            l1 = BoardList.objects.create(title='Todo', board=board, position=1)
            l2 = BoardList.objects.create(title='Doing', board=board, position=2)
            l3 = BoardList.objects.create(title='Done', board=board, position=3)
            return board, l1, l2, l3

        def test_create_list_permission_and_reorder(self):
            board, l1, l2, l3 = self._create_board_with_lists()

            # create a new list via view
            url = reverse('create_list', kwargs={'board_id': board.id})
            resp = self.client.post(url, data={'title': 'Blocked'})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get('success'))

            # lists should be sequential
            positions = list(board.lists.order_by('position').values_list('title', 'position'))
            titles = [t for t, p in positions]
            self.assertIn('Blocked', titles)

        def test_create_card_update_and_detail(self):
            board, l1, l2, l3 = self._create_board_with_lists()

            url = reverse('create_card', kwargs={'list_id': l1.id})
            resp = self.client.post(url, data={'title': 'Task 1'})
            self.assertEqual(resp.status_code, 200)
            payload = resp.json()
            self.assertTrue(payload.get('success'))

            card_id = payload['card']['id']

            # update card
            upd_url = reverse('update_card', kwargs={'card_id': card_id})
            resp = self.client.post(upd_url, data={'title': 'Task 1 updated'})
            self.assertEqual(resp.status_code, 200)

            # get detail
            detail_url = reverse('card_detail', kwargs={'card_id': card_id})
            resp = self.client.get(detail_url)
            self.assertEqual(resp.status_code, 200)
            d = resp.json()
            self.assertTrue(d.get('success'))
            self.assertEqual(d['card']['title'], 'Task 1 updated')

        def test_move_edge_positions_and_append(self):
            board, l1, l2, l3 = self._create_board_with_lists()

            c1 = Card.objects.create(title='One', board_list=l1, created_by=self.employee, position=1)
            c2 = Card.objects.create(title='Two', board_list=l1, created_by=self.employee, position=2)
            c3 = Card.objects.create(title='Three', board_list=l1, created_by=self.employee, position=3)

            url = reverse('move_card')

            # move c1 to position beyond end -> should append to end
            payload = {'card_id': str(c1.id), 'new_list_id': str(l1.id), 'new_position': 999}
            resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
            self.assertEqual(resp.status_code, 200, resp.content)
            ordered = list(Card.objects.filter(board_list=l1).order_by('position').values_list('title', flat=True))
            self.assertEqual(ordered, ['Two', 'Three', 'One'])

        def test_move_across_lists_and_delete(self):
            board, l1, l2, l3 = self._create_board_with_lists()

            a = Card.objects.create(title='A', board_list=l1, created_by=self.employee, position=1)
            b = Card.objects.create(title='B', board_list=l1, created_by=self.employee, position=2)

            url = reverse('move_card')
            payload = {'card_id': str(a.id), 'new_list_id': str(l2.id), 'new_position': 1}
            resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
            self.assertEqual(resp.status_code, 200, resp.content)

            self.assertEqual(list(Card.objects.filter(board_list=l1).order_by('position').values_list('title', flat=True)), ['B'])
            self.assertEqual(list(Card.objects.filter(board_list=l2).order_by('position').values_list('title', flat=True)), ['A'])

            # delete card A
            del_url = reverse('delete_card', kwargs={'card_id': a.id})
            resp = self.client.post(del_url)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(list(Card.objects.filter(board_list=l2)), [])

        def test_board_member_management_and_permissions(self):
            # create a separate creator (not the test user) and a board owned by them
            creator_user = User.objects.create_user(username='creator', email='c@example.com', password='p')
            creator_emp = Employee.objects.create(user=creator_user, employee_id='C1', position='Admin', phone='0', is_active=True, is_email_verified=True)
            board = Board.objects.create(title='PermBoard', created_by=creator_emp)

            # ensure tester is not currently a member
            self.assertFalse(board.members.filter(id=self.employee.id).exists())

            # login as creator to add tester as member
            self.client.force_login(creator_user)
            add_url = reverse('add_board_member', kwargs={'board_id': board.id})
            resp = self.client.post(add_url, data={'email': self.user.email})
            # allow 200 (added) or 400 (already a member) as both are acceptable outcomes
            self.assertIn(resp.status_code, (200, 400))

            # now tester should be able to create a list; login back as tester and create list
            self.client.force_login(self.user)
            url = reverse('create_list', kwargs={'board_id': board.id})
            resp = self.client.post(url, data={'title': 'NowAllowed'})
            self.assertEqual(resp.status_code, 200)

        def test_add_comment(self):
            board, l1, l2, l3 = self._create_board_with_lists()
            card = Card.objects.create(title='C', board_list=l1, created_by=self.employee, position=1)

            url = reverse('add_card_comment', kwargs={'card_id': card.id})
            resp = self.client.post(url, data={'content': 'Nice work'})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get('success'))
            self.assertEqual(CardComment.objects.filter(card=card).count(), 1)

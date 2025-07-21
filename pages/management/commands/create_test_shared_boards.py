from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import Employee, Board, BoardShare
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create test shared boards for debugging'

    def handle(self, *args, **options):
        self.stdout.write('Creating test shared boards...')
        
        # Get all employees
        employees = Employee.objects.all()
        
        if employees.count() < 2:
            self.stdout.write(self.style.ERROR('Need at least 2 employees to create shared boards'))
            return
        
        # Get first two employees
        employee1 = employees.first()
        employee2 = employees[1] if employees.count() > 1 else employees.first()
        
        self.stdout.write(f'Employee 1: {employee1.user.username}')
        self.stdout.write(f'Employee 2: {employee2.user.username}')
        
        # Create a test board by employee1
        test_board = Board.objects.create(
            title='Test Shared Board',
            description='This is a test board to verify sharing functionality',
            created_by=employee1,
            is_public=False
        )
        
        self.stdout.write(f'Created board: {test_board.title} (ID: {test_board.id})')
        
        # Share the board with employee2
        board_share, created = BoardShare.objects.get_or_create(
            board=test_board,
            shared_with=employee2,
            defaults={
                'shared_by': employee1,
                'permission': 'view'
            }
        )
        
        if created:
            self.stdout.write(f'Shared board with {employee2.user.username}')
        else:
            self.stdout.write(f'Board already shared with {employee2.user.username}')
        
        # Verify the sharing
        shared_count = BoardShare.objects.filter(shared_with=employee2).count()
        self.stdout.write(f'Total boards shared with {employee2.user.username}: {shared_count}')
        
        # Show all BoardShare records
        all_shares = BoardShare.objects.all()
        self.stdout.write(f'Total BoardShare records in database: {all_shares.count()}')
        
        for share in all_shares:
            self.stdout.write(f'  - Board "{share.board.title}" shared by {share.shared_by.user.username} with {share.shared_with.user.username}')
        
        self.stdout.write(self.style.SUCCESS('Test shared boards created successfully!'))

from django.core.management.base import BaseCommand
from pages.models import BoardList, Card
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix position conflicts in board cards'
    
    def handle(self, *args, **options):
        self.stdout.write('Fixing card position conflicts...')
        
        fixed_lists = 0
        fixed_cards = 0
        
        for board_list in BoardList.objects.all():
            cards = board_list.cards.all().order_by('position', 'created_at')
            
            # Check if positions are correct
            needs_fix = False
            positions_seen = set()
            
            for card in cards:
                if card.position in positions_seen or card.position <= 0:
                    needs_fix = True
                    break
                positions_seen.add(card.position)
            
            if needs_fix:
                self.stdout.write(f'Fixing positions in list: {board_list.title}')
                
                with transaction.atomic():
                    for index, card in enumerate(cards, 1):
                        if card.position != index:
                            card.position = index
                            card.save()
                            fixed_cards += 1
                
                fixed_lists += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Fixed {fixed_cards} cards in {fixed_lists} lists'
            )
        )

"""
Management command to bootstrap transaction logging system
Creates default states and transaction types
"""
from django.core.management.base import BaseCommand
from billing_service.billing.models.transaction_log import State, TransactionType


class Command(BaseCommand):
    help = "Bootstrap transaction logging system with default states and transaction types"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bootstrapping transaction logging system..."))
        
        # Bootstrap States
        self.stdout.write("Creating default states...")
        State.bootstrap_defaults()
        state_count = State.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✓ {state_count} states created/verified"))
        
        # Bootstrap Transaction Types
        self.stdout.write("Creating default transaction types...")
        TransactionType.bootstrap_defaults()
        txn_type_count = TransactionType.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✓ {txn_type_count} transaction types created/verified"))
        
        # Display summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("Transaction logging system ready!"))
        self.stdout.write("="*50)
        
        # List states
        self.stdout.write("\nAvailable States:")
        for state in State.objects.all():
            self.stdout.write(f"  - {state.name}")
        
        # List transaction types by category
        self.stdout.write("\nAvailable Transaction Types:")
        categories = TransactionType.objects.values_list('category', flat=True).distinct()
        for category in categories:
            self.stdout.write(f"\n  {category.upper()}:")
            txn_types = TransactionType.objects.filter(category=category)
            for txn_type in txn_types:
                self.stdout.write(f"    - {txn_type.name}")
        
        self.stdout.write("\n" + self.style.SUCCESS("Bootstrap complete!"))

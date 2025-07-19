from django.core.management.base import BaseCommand
from pages.models import StorageManager, Employee
from django.conf import settings
import subprocess
import os
import shutil

class Command(BaseCommand):
    help = 'Configure and test application storage limits for shared VM environments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--set-limit',
            type=float,
            help='Set application storage limit in GB (e.g., --set-limit 0.5 for 512MiB)',
        )
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Show current storage configuration and usage',
        )
        parser.add_argument(
            '--test-scenarios',
            action='store_true',
            help='Test different storage limit scenarios',
        )
        parser.add_argument(
            '--detect-quota',
            action='store_true',
            help='Try to detect actual disk quota using system commands',
        )
        parser.add_argument(
            '--analyze-usage',
            action='store_true',
            help='Analyze actual disk usage like PythonAnywhere du command',
        )

    def handle(self, *args, **options):
        if options['set_limit']:
            self.set_storage_limit(options['set_limit'])
        elif options['show_current']:
            self.show_current_config()
        elif options['test_scenarios']:
            self.test_scenarios()
        elif options['detect_quota']:
            self.detect_actual_quota()
        elif options['analyze_usage']:
            self.analyze_disk_usage()
        else:
            self.show_current_config()

    def set_storage_limit(self, limit_gb):
        """Set the application storage limit"""
        self.stdout.write(f"Setting application storage limit to {limit_gb} GB...")
        
        # Note: This would require modifying settings.py
        self.stdout.write(
            self.style.WARNING(
                f"To set the limit, add this to your settings.py:\n"
                f"APPLICATION_STORAGE_LIMIT_GB = {limit_gb}"
            )
        )
        
        # Calculate what quotas would be with this limit
        if limit_gb:
            reserved_space = 1  # 1GB for website
            available_for_users = max(0, limit_gb - reserved_space)
            active_users = Employee.objects.filter(is_active=True).count()
            
            if active_users > 0:
                quota_per_user = available_for_users / active_users
                self.stdout.write(f"With {limit_gb}GB limit:")
                self.stdout.write(f"  - Reserved for website: {reserved_space}GB")
                self.stdout.write(f"  - Available for users: {available_for_users}GB")
                self.stdout.write(f"  - Active users: {active_users}")
                self.stdout.write(f"  - Quota per user: {quota_per_user:.2f}GB")

    def show_current_config(self):
        """Show current storage configuration"""
        self.stdout.write(self.style.SUCCESS("Current Storage Configuration"))
        self.stdout.write("=" * 50)
        
        # Get current setting
        limit = getattr(settings, 'APPLICATION_STORAGE_LIMIT_GB', None)
        
        if limit:
            self.stdout.write(f"✅ Application storage limit: {limit} GB")
            self.stdout.write("   (Using configured limit instead of full VM disk)")
        else:
            self.stdout.write("⚠️  No application storage limit set")
            self.stdout.write("   (Using full VM disk space - may be inaccurate on shared VMs)")
        
        # Get current storage info
        storage_info = StorageManager.get_system_storage_info()
        
        self.stdout.write(f"\nCurrent Storage Status:")
        self.stdout.write(f"  - Total: {storage_info['total'] / (1024**3):.2f} GB")
        self.stdout.write(f"  - Used: {storage_info['used'] / (1024**3):.2f} GB")
        self.stdout.write(f"  - Free: {storage_info['free'] / (1024**3):.2f} GB")
        
        if storage_info.get('is_limited'):
            self.stdout.write(f"  - Configured limit: {storage_info['configured_limit_gb']} GB")
            self.stdout.write(f"  - Actual VM disk free: {storage_info['disk_free'] / (1024**3):.2f} GB")
        
        # Show user info
        stats = StorageManager.get_storage_stats()
        self.stdout.write(f"\nUser Storage:")
        self.stdout.write(f"  - Active users: {stats['active_users']}")
        self.stdout.write(f"  - Quota per user: {stats['quota_per_user_display']}")
        self.stdout.write(f"  - Total allocated: {stats['total_allocated_display']}")
        self.stdout.write(f"  - Total used by users: {stats['total_user_storage_display']}")

    def test_scenarios(self):
        """Test different storage limit scenarios"""
        self.stdout.write(self.style.SUCCESS("Testing Storage Limit Scenarios"))
        self.stdout.write("=" * 50)
        
        active_users = Employee.objects.filter(is_active=True).count()
        current_usage = Employee.objects.filter(is_active=True).aggregate(
            total=sum([u.storage_used for u in Employee.objects.filter(is_active=True)])
        )
        
        # Test different limits
        test_limits = [10, 25, 50, 100, 200, None]
        
        for limit in test_limits:
            if limit is None:
                # Get actual VM disk space
                storage_info = StorageManager.get_system_storage_info()
                vm_total_gb = storage_info['disk_total'] / (1024**3)
                self.stdout.write(f"\nScenario: No limit (Full VM disk - {vm_total_gb:.1f} GB)")
                available_for_users = vm_total_gb - 1  # 1GB reserved
            else:
                self.stdout.write(f"\nScenario: {limit} GB application limit")
                available_for_users = max(0, limit - 1)  # 1GB reserved
            
            if active_users > 0 and available_for_users > 0:
                quota_per_user = available_for_users / active_users
                self.stdout.write(f"  ✅ Quota per user: {quota_per_user:.2f} GB")
                
                if quota_per_user < 1:
                    self.stdout.write(f"  ⚠️  WARNING: Less than 1GB per user!")
                elif quota_per_user > 50:
                    self.stdout.write(f"  ⚠️  Very large quota - consider if this is intentional")
            else:
                self.stdout.write(f"  ❌ No space available for users")

        self.stdout.write(f"\n💡 Recommendations:")
        self.stdout.write(f"   - For shared VMs: Set APPLICATION_STORAGE_LIMIT_GB to a reasonable value")
        self.stdout.write(f"   - For dedicated VMs: Keep APPLICATION_STORAGE_LIMIT_GB = None")
        self.stdout.write(f"   - Consider your actual storage needs vs. VM disk space")

    def detect_actual_quota(self):
        """Try to detect actual disk quota using system commands (PythonAnywhere compatible)"""
        self.stdout.write(self.style.SUCCESS("Detecting Actual Disk Quota (PythonAnywhere Style)"))
        self.stdout.write("=" * 60)
        
        try:
            home_dir = os.path.expanduser('~')
            self.stdout.write(f"Analyzing account directory: {home_dir}")
            
            # Method 1: Try quota command (works on PythonAnywhere)
            self.stdout.write(f"\n1. Checking for disk quota information:")
            try:
                # PythonAnywhere uses quota command
                result = subprocess.run(['quota', '-u'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    self.stdout.write("   ✅ Quota information found:")
                    self.stdout.write(f"   {result.stdout}")
                else:
                    self.stdout.write("   ❌ No quota command available (not on PythonAnywhere)")
            except Exception as e:
                self.stdout.write(f"   ❌ Quota command not available: {str(e)}")
            
            # Method 2: Use PythonAnywhere's disk usage command equivalent
            self.stdout.write(f"\n2. Calculating actual usage (PythonAnywhere du equivalent):")
            
            # This mimics: du -s -B 1 /tmp ~/.[!.]* ~/* | awk '{s+=$1}END{print s}'
            total_usage = self.pythonanywhere_disk_usage()
            
            if total_usage:
                usage_gb = total_usage / (1024**3)
                usage_mb = total_usage / (1024**2)
                usage_mib = total_usage / (1024**2 * 1.048576)  # True MiB for PythonAnywhere
                
                self.stdout.write(f"   Total usage: {usage_gb:.3f} GB ({usage_mb:.1f} MB / {usage_mib:.1f} MiB)")
                
                # PythonAnywhere specific quota levels
                pythonanywhere_quotas = {
                    'Free Account': {'quota_mib': 512, 'quota_gb': 0.5},
                    'Hacker Plan': {'quota_mib': 3072, 'quota_gb': 3.0},  # 3GB
                    'Web Developer': {'quota_mib': 10240, 'quota_gb': 10.0},  # 10GB
                    'Web Developer Plus': {'quota_mib': 20480, 'quota_gb': 20.0},  # 20GB
                }
                
                self.stdout.write(f"\n3. PythonAnywhere quota comparison:")
                for plan, limits in pythonanywhere_quotas.items():
                    percentage = (usage_mib / limits['quota_mib']) * 100
                    if percentage < 70:
                        status = "✅ Safe"
                        color = self.style.SUCCESS
                    elif percentage < 90:
                        status = "⚠️  Warning"
                        color = self.style.WARNING
                    else:
                        status = "❌ Critical"
                        color = self.style.ERROR
                    
                    self.stdout.write(color(
                        f"   {plan}: {percentage:.1f}% used "
                        f"({usage_mib:.0f}/{limits['quota_mib']} MiB) - {status}"
                    ))
                
                # Recommend setting for APPLICATION_STORAGE_LIMIT_GB
                self.stdout.write(f"\n4. Configuration recommendation:")
                for plan, limits in pythonanywhere_quotas.items():
                    if usage_mib < limits['quota_mib'] * 0.8:  # If using less than 80%
                        suggested_limit = limits['quota_gb'] * 0.9  # Use 90% of quota for app
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"   💡 If on {plan}, set: APPLICATION_STORAGE_LIMIT_GB = {suggested_limit:.1f}"
                            )
                        )
                        break
            
        except Exception as e:
            self.stdout.write(f"❌ Error detecting quota: {str(e)}")

    def pythonanywhere_disk_usage(self):
        """Calculate disk usage using PythonAnywhere's method"""
        try:
            home_dir = os.path.expanduser('~')
            total_size = 0
            
            # PythonAnywhere checks: /tmp, hidden files (~/.something), and regular files (~/* )
            paths_to_check = []
            
            # Add /tmp if it exists and is accessible
            tmp_dir = '/tmp'
            if os.path.exists(tmp_dir) and os.access(tmp_dir, os.R_OK):
                paths_to_check.append(tmp_dir)
            
            # Add hidden files and directories in home (~/.*)
            try:
                for item in os.listdir(home_dir):
                    if item.startswith('.') and item not in ['.', '..']:
                        path = os.path.join(home_dir, item)
                        paths_to_check.append(path)
            except PermissionError:
                pass
            
            # Add regular files and directories in home (~/*)
            try:
                for item in os.listdir(home_dir):
                    if not item.startswith('.'):
                        path = os.path.join(home_dir, item)
                        paths_to_check.append(path)
            except PermissionError:
                pass
            
            # Calculate total size
            for path in paths_to_check:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        try:
                            total_size += os.path.getsize(path)
                        except (OSError, IOError):
                            continue
                    elif os.path.isdir(path):
                        total_size += self.get_directory_size(path)
            
            return total_size
            
        except Exception as e:
            self.stdout.write(f"   ❌ Error calculating usage: {str(e)}")
            return None

    def analyze_disk_usage(self):
        """Analyze disk usage exactly like PythonAnywhere's du command"""
        self.stdout.write(self.style.SUCCESS("Disk Usage Analysis (PythonAnywhere Method)"))
        self.stdout.write("=" * 60)
        self.stdout.write("Replicating: du -hs /tmp ~/.[!.]* ~/* | sort -h")
        self.stdout.write("-" * 60)
        
        try:
            home_dir = os.path.expanduser('~')
            usage_data = []
            
            # 1. Check /tmp directory (PythonAnywhere includes this)
            tmp_dir = '/tmp'
            if os.path.exists(tmp_dir):
                try:
                    size = self.get_directory_size(tmp_dir)
                    if size > 0:
                        usage_data.append(('/tmp', size))
                except Exception:
                    pass
            
            # 2. Check hidden files and directories (~/.[!.]*)
            # This means files/dirs starting with . but not . or ..
            try:
                for item in os.listdir(home_dir):
                    if item.startswith('.') and item not in ['.', '..']:
                        path = os.path.join(home_dir, item)
                        try:
                            if os.path.isfile(path):
                                size = os.path.getsize(path)
                            else:
                                size = self.get_directory_size(path)
                            
                            if size > 0:
                                usage_data.append((f"~/{item}", size))
                        except Exception:
                            continue
            except PermissionError:
                self.stdout.write("   ❌ Cannot access home directory")
            
            # 3. Check regular files and directories (~/* )
            try:
                for item in os.listdir(home_dir):
                    if not item.startswith('.'):
                        path = os.path.join(home_dir, item)
                        try:
                            if os.path.isfile(path):
                                size = os.path.getsize(path)
                            else:
                                size = self.get_directory_size(path)
                            
                            if size > 0:
                                usage_data.append((f"~/{item}", size))
                        except Exception:
                            continue
            except PermissionError:
                pass
            
            # Sort by size (like sort -h)
            usage_data.sort(key=lambda x: x[1])
            
            # Display results in PythonAnywhere format
            total_size = 0
            for path, size in usage_data:
                total_size += size
                # Show size in human readable format
                self.stdout.write(f"{self.format_size_pa(size):>8} {path}")
            
            self.stdout.write("-" * 60)
            self.stdout.write(f"{self.format_size_pa(total_size):>8} TOTAL")
            
            # Show equivalent to: du -s -B 1 /tmp ~/.[!.]* ~/* | awk '{s+=$1}END{print s}'
            self.stdout.write(f"\nTotal bytes (du -s -B 1 equivalent): {total_size}")
            
            # PythonAnywhere specific cleanup recommendations
            self.stdout.write(f"\n" + "="*60)
            self.stdout.write(f"🧹 PythonAnywhere Cleanup Commands:")
            self.stdout.write(f"="*60)
            
            # Find largest directories to suggest cleanup
            large_dirs = [(path, size) for path, size in usage_data if size > 10*1024*1024]  # >10MB
            
            if large_dirs:
                self.stdout.write(f"\n📊 Largest directories (>10MB):")
                for path, size in sorted(large_dirs, key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (size / total_size) * 100
                    self.stdout.write(f"   {self.format_size_pa(size):>8} {path} ({percentage:.1f}% of total)")
            
            self.stdout.write(f"\n🔧 Cleanup commands (run in PythonAnywhere bash console):")
            self.stdout.write(f"   1. Clear /tmp:           rm -rf /tmp/* /tmp/.*")
            self.stdout.write(f"   2. Clear cache:          rm -rf ~/.cache/*")
            self.stdout.write(f"   3. Clear pip cache:      pip cache purge")
            self.stdout.write(f"   4. Clear Python cache:   find ~ -name '__pycache__' -exec rm -rf {{}} +")
            self.stdout.write(f"   5. Remove old venvs:     rmvirtualenv old-env-name")
            self.stdout.write(f"   6. Uninstall packages:   pip3.x uninstall package-name --user")
            
            # Check for common space wasters
            space_wasters = []
            for path, size in usage_data:
                if 'cache' in path.lower() or '__pycache__' in path or '.pyc' in path:
                    space_wasters.append((path, size))
            
            if space_wasters:
                total_wasted = sum(size for _, size in space_wasters)
                self.stdout.write(f"\n💡 Potential space savings: {self.format_size_pa(total_wasted)}")
                
        except Exception as e:
            self.stdout.write(f"❌ Error analyzing usage: {str(e)}")

    def format_size_pa(self, size_bytes):
        """Format size in PythonAnywhere style (like du -h)"""
        if size_bytes == 0:
            return "0"
        
        # PythonAnywhere uses 1024-based units
        for unit in ['B', 'K', 'M', 'G', 'T']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{int(size_bytes)}"
                else:
                    return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f}P"

    def calculate_actual_usage(self):
        """Calculate actual disk usage in bytes"""
        try:
            home_dir = os.path.expanduser('~')
            total_size = 0
            
            for root, dirs, files in os.walk(home_dir):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue  # Skip files we can't access
                        
            return total_size
        except Exception:
            return None

    def get_directory_size(self, directory):
        """Get size of a directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue
        except Exception:
            pass
        return total_size

    def format_size(self, size_bytes):
        """Format size in human readable format"""
        if size_bytes == 0:
            return "0B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f}TB"

"""
File Management Views - Drive-like interface for file management
"""
import os
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Sum, F
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from .models import FileDocument, FileFolder, FileVersion, FileShare, FileActivity, Employee, AIFileAnalysis
from .forms import FolderForm, FileUploadForm, FileShareForm, FileSearchForm
from .ai_assistant import create_free_ai_assistant
import json
from datetime import datetime, timedelta


@login_required
def file_manager(request):
    """Main file manager view - Drive-like interface"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')
    
    # Check if showing only shared files or recent files
    show_shared_only = request.GET.get('shared') == 'true'
    show_recent_only = request.GET.get('recent') == 'true'
    
    # Get current folder
    folder_id = request.GET.get('folder')
    current_folder = None
    if folder_id and not show_shared_only and not show_recent_only:  # Don't navigate folders in special views
        # Allow access to folders created by user OR shared with user
        current_folder = FileFolder.objects.filter(
            Q(id=folder_id) & 
            (Q(created_by=employee) | Q(shared_with=employee))
        ).first()
        if not current_folder:
            messages.error(request, 'Folder not found or access denied.')
            return redirect('file_manager')
    
    # Get breadcrumb navigation
    breadcrumbs = []
    if current_folder and not show_shared_only and not show_recent_only:
        folder = current_folder
        while folder:
            breadcrumbs.append(folder)
            folder = folder.parent
        breadcrumbs.reverse()
    
    # Get files and folders based on view mode
    if show_shared_only:
        # Show only shared files (no folder navigation)
        folders = FileFolder.objects.none()  # No folders in shared view
        
        # Get files shared through both methods:
        # 1. Direct shared_with ManyToMany relationship
        # 2. Through FileShare model
        shared_files_direct = FileDocument.objects.filter(
            shared_with=employee
        ).exclude(uploaded_by=employee)
        
        shared_files_through_share = FileDocument.objects.filter(
            shares__shared_with=employee
        ).exclude(uploaded_by=employee)
        
        public_files = FileDocument.objects.filter(
            is_public=True
        ).exclude(uploaded_by=employee)
        
        # Combine all shared files and remove duplicates
        files = (shared_files_direct | shared_files_through_share | public_files).distinct()
    elif show_recent_only:
        # Show only recent files (no folder navigation)
        folders = FileFolder.objects.none()  # No folders in recent view
        files = FileDocument.objects.filter(
            Q(uploaded_by=employee) | Q(shared_with=employee) | Q(shares__shared_with=employee)
        ).order_by('-last_accessed')[:20].distinct()  # Show last 20 accessed files
    elif current_folder:
        # Show folders that are children of current folder AND user has access to
        folders = FileFolder.objects.filter(
            Q(parent=current_folder) & 
            (Q(created_by=employee) | Q(shared_with=employee))
        ).distinct()
        
        # Show files in current folder that user has access to
        files = FileDocument.objects.filter(
            Q(folder=current_folder) & 
            (Q(uploaded_by=employee) | Q(shared_with=employee) | Q(shares__shared_with=employee))
        ).distinct()
    else:
        # Root level - show user's folders and folders shared with them
        folders = FileFolder.objects.filter(
            Q(parent=None) & 
            (Q(created_by=employee) | Q(shared_with=employee))
        ).distinct()
        
        # Root level - show user's files and files shared with them (no folder)
        files = FileDocument.objects.filter(
            Q(folder=None) & 
            (Q(uploaded_by=employee) | Q(shared_with=employee) | Q(shares__shared_with=employee))
        ).distinct()
    
    # Get shared files (for sidebar statistics)
    shared_files_direct = FileDocument.objects.filter(
        shared_with=employee
    ).exclude(uploaded_by=employee)
    
    shared_files_through_share = FileDocument.objects.filter(
        shares__shared_with=employee
    ).exclude(uploaded_by=employee)
    
    public_files = FileDocument.objects.filter(
        is_public=True
    ).exclude(uploaded_by=employee)
    
    # Combine all shared files for sidebar count
    shared_files = (shared_files_direct | shared_files_through_share | public_files).distinct()
    
    # Get recent files
    recent_files = FileDocument.objects.filter(
        Q(uploaded_by=employee) | Q(shared_with=employee) | Q(shares__shared_with=employee)
    ).order_by('-last_accessed')[:10].distinct()
    
    # Get file statistics
    total_files = FileDocument.objects.filter(uploaded_by=employee).count()
    total_size = sum(f.file_size for f in FileDocument.objects.filter(uploaded_by=employee))
    
    # Get all accessible folders for upload dropdown
    all_folders = FileFolder.objects.filter(
        Q(created_by=employee) | Q(shared_with=employee)
    ).distinct().order_by('name')

    context = {
        'employee': employee,
        'current_folder': current_folder,
        'breadcrumbs': breadcrumbs,
        'folders': folders,
        'files': files,  # Use original files without AI analysis
        'shared_files': shared_files,
        'recent_files': recent_files,
        'total_files': total_files,
        'total_size': total_size,
        'all_folders': all_folders,  # For dropdown in upload form
        'upload_form': FileUploadForm(user=request.user),
        'folder_form': FolderForm(user=request.user),
        'search_form': FileSearchForm(),
        'show_shared_only': show_shared_only,  # Add this to control template display
        'show_recent_only': show_recent_only,  # Add this to control template display
    }
    
    return render(request, 'employee/file_manager.html', context)


@login_required
@require_http_methods(["GET"])
def get_file_analysis(request, file_id):
    """AJAX endpoint to get AI analysis for a specific file"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_obj = get_object_or_404(FileDocument, 
                                   id=file_id,
                                   uploaded_by=employee)
        
        # Initialize AI analyzer
        analyzer, bot = create_free_ai_assistant()
        
        # Get file analysis
        file_path = file_obj.get_file_path()
        if file_path and os.path.exists(file_path):
            analysis = analyzer.analyze_file(file_path, file_obj.name)
            
            # Clean up for JSON response
            if isinstance(analysis.get('analysis_date'), datetime):
                analysis['analysis_date'] = analysis['analysis_date'].isoformat()
            
            return JsonResponse({
                'success': True,
                'analysis': analysis
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'File not accessible'
            })
            
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def create_folder(request):
    """Create a new folder"""
    if request.method == 'POST':
        try:
            employee = Employee.objects.get(user=request.user)
            form = FolderForm(request.POST, user=request.user)
            
            if form.is_valid():
                folder = form.save(commit=False)
                folder.created_by = employee
                folder.save()
                
                messages.success(request, f'Folder "{folder.name}" created successfully.')
                return JsonResponse({'success': True, 'message': 'Folder created successfully'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Employee profile not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def upload_file(request):
    """Upload files with real-time storage quota enforcement"""
    if request.method == 'POST':
        try:
            employee = Employee.objects.get(user=request.user)
            uploaded_files = []
            
            # STEP 1: Update storage quotas first to ensure we have the latest allocation
            from .models import StorageManager
            try:
                quota_result = StorageManager.update_all_user_quotas()
                print(f"[QUOTA UPDATE] Updated {quota_result['updated_users']} users with latest quotas")
            except Exception as e:
                print(f"[QUOTA WARNING] Failed to update quotas: {str(e)}")
                # Continue with existing quota if update fails
            
            # Refresh employee data to get updated quota
            employee.refresh_from_db()
            
            # STEP 2: Ensure user has a quota set
            if employee.storage_quota is None or employee.storage_quota == 0:
                employee.storage_quota = StorageManager.calculate_user_quota()
                employee.save()
                print(f"[QUOTA SET] Set initial quota for {employee.get_full_name()}: {employee.get_storage_quota_display()}")
            
            # STEP 3: Calculate total size of files being uploaded
            total_upload_size = sum(file.size for file in request.FILES.getlist('files'))
            
            # STEP 4: Check if user has enough storage space after quota update
            if not employee.can_upload_file(total_upload_size):
                available_space = employee.get_available_storage()
                
                # Provide detailed error message with current quota info
                storage_info = {
                    'current_used': employee.get_storage_used_display(),
                    'total_quota': employee.get_storage_quota_display(),
                    'available': employee._format_bytes(available_space),
                    'required': employee._format_bytes(total_upload_size),
                    'percentage_used': employee.get_storage_percentage()
                }
                
                error_message = (
                    f"Upload denied: Insufficient storage space.\n"
                    f"• You need: {storage_info['required']}\n"
                    f"• Available: {storage_info['available']}\n"
                    f"• Current usage: {storage_info['current_used']} / {storage_info['total_quota']} "
                    f"({storage_info['percentage_used']:.1f}%)\n"
                    f"• Storage quotas were updated to latest allocation before this check."
                )
                
                return JsonResponse({
                    'success': False, 
                    'message': error_message,
                    'storage_error': True,
                    'storage_info': storage_info,
                    'quota_updated': True
                })
            
            # Handle multiple file uploads
            for file in request.FILES.getlist('files'):
                # Create file document
                file_doc = FileDocument(
                    name=file.name,
                    file=file,
                    file_size=file.size,
                    mime_type=file.content_type,
                    uploaded_by=employee
                )
                
                # Set folder if provided
                folder_id = request.POST.get('folder')
                if folder_id:
                    try:
                        # Allow access to folders created by user OR shared with user
                        folder = FileFolder.objects.filter(
                            Q(id=folder_id) & 
                            (Q(created_by=employee) | Q(shared_with=employee))
                        ).first()
                        if folder:
                            file_doc.folder = folder
                    except (FileFolder.DoesNotExist, ValueError):
                        pass
                
                # Set file type based on mime type
                if file.content_type:
                    if file.content_type.startswith('image/'):
                        file_doc.file_type = 'image'
                    elif file.content_type.startswith('video/'):
                        file_doc.file_type = 'video'
                    elif file.content_type.startswith('audio/'):
                        file_doc.file_type = 'audio'
                    elif file.content_type == 'application/pdf':
                        file_doc.file_type = 'pdf'
                    elif file.content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                        file_doc.file_type = 'document'
                    elif file.content_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                        file_doc.file_type = 'spreadsheet'
                    elif file.content_type in ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
                        file_doc.file_type = 'presentation'
                
                # Set other fields
                file_doc.description = request.POST.get('description', '')
                file_doc.tags = request.POST.get('tags', '')
                file_doc.is_public = request.POST.get('is_public') == 'on'
                
                file_doc.save()
                
                # AI Analysis - Run in background
                try:
                    analyzer, _ = create_free_ai_assistant()
                    analysis = analyzer.analyze_file(file_doc.file.path, file_doc.name)
                    
                    # Update file with AI insights
                    if analysis.get('summary'):
                        if not file_doc.description:
                            file_doc.description = analysis['summary']
                    
                    if analysis.get('key_topics'):
                        if not file_doc.tags:
                            file_doc.tags = ', '.join(analysis['key_topics'][:5])
                    
                    # Update category based on AI analysis
                    if analysis.get('category'):
                        # You could add a category field to FileDocument model
                        pass
                    
                    file_doc.save()
                except Exception as e:
                    # Don't fail upload if AI analysis fails
                    print(f"AI analysis failed: {str(e)}")
                
                # ===== AI WORKFLOW INTEGRATION =====
                try:
                    from .ai_workflow_service import get_ai_workflow_service
                    
                    ai_service = get_ai_workflow_service()
                    workflow_result = ai_service.handle_file_upload(file_doc, employee)
                    
                    if workflow_result['success']:
                        print(f"[AI WORKFLOWS] Executed {workflow_result['executed_workflows']} workflows, "
                              f"created {workflow_result['notifications_created']} notifications")
                    else:
                        print(f"[AI WORKFLOWS] Error: {workflow_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    # Don't fail upload if AI workflows fail
                    print(f"[AI WORKFLOWS] Failed to process workflows: {str(e)}")
                # ===== END AI WORKFLOW INTEGRATION =====
                
                # Log activity
                FileActivity.objects.create(
                    document=file_doc,
                    user=employee,
                    action='upload',
                    details=f'Uploaded file: {file.name}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                uploaded_files.append(file_doc.name)
            
            # Update user's storage usage
            employee.update_storage_used()
            
            # Get updated storage information for response
            updated_storage_info = {
                'used': employee.get_storage_used_display(),
                'quota': employee.get_storage_quota_display(),
                'percentage': employee.get_storage_percentage(),
                'available': employee._format_bytes(employee.get_available_storage())
            }
            
            success_message = (
                f'Successfully uploaded {len(uploaded_files)} file(s). '
                f'Storage: {updated_storage_info["used"]} / {updated_storage_info["quota"]} used '
                f'({updated_storage_info["percentage"]:.1f}%)'
            )
            
            messages.success(request, success_message)
            return JsonResponse({
                'success': True, 
                'files': uploaded_files,
                'storage_info': updated_storage_info,
                'quota_updated': True,
                'message': success_message
            })
            
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Employee profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def test_file_serve(request, file_id):
    """Test file serving - for debugging"""
    try:
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        import os
        file_path = file_doc.file.path
        
        # Basic checks
        if not os.path.exists(file_path):
            return HttpResponse(f"File not found: {file_path}", status=404)
        
        file_size = os.path.getsize(file_path)
        
        # Try to read and serve the file
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                response = HttpResponse(content, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{file_doc.name}"'
                response['Content-Length'] = str(file_size)
                return response
        except Exception as e:
            return HttpResponse(f"Error reading file: {str(e)}", status=500)
            
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def serve_file(request, file_id):
    """Serve a file for preview/viewing"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check permissions
        if not (file_doc.uploaded_by == employee or 
                employee in file_doc.shared_with.all() or 
                file_doc.is_public):
            raise Http404("File not found")
        
        # Update access tracking
        file_doc.last_accessed = timezone.now()
        file_doc.save()
        
        # Log activity
        FileActivity.objects.create(
            document=file_doc,
            user=employee,
            action='view',
            details=f'Viewed file: {file_doc.name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Serve file for viewing (not download)
        import os
        if not os.path.exists(file_doc.file.path):
            raise Http404("File not found on disk")
        
        # Set proper MIME type based on file extension if not set
        mime_type = file_doc.mime_type
        if not mime_type:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_doc.file.path)
            if not mime_type:
                mime_type = 'application/octet-stream'
        
        with open(file_doc.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=mime_type)
            response['Content-Disposition'] = f'inline; filename="{file_doc.name}"'
            response['Content-Length'] = str(os.path.getsize(file_doc.file.path))
            response['Accept-Ranges'] = 'bytes'
            return response
        
    except Employee.DoesNotExist:
        raise Http404("Employee profile not found")
    except Exception as e:
        import traceback
        print(f"Error serving file: {str(e)}")
        print(traceback.format_exc())
        raise Http404(f"Error serving file: {str(e)}")


@login_required
def download_file(request, file_id):
    """Download a file"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check permissions
        if not (file_doc.uploaded_by == employee or 
                employee in file_doc.shared_with.all() or 
                file_doc.is_public):
            raise Http404("File not found")
        
        # Update access tracking
        file_doc.last_accessed = timezone.now()
        file_doc.download_count += 1
        file_doc.save()
        
        # Log activity
        FileActivity.objects.create(
            document=file_doc,
            user=employee,
            action='download',
            details=f'Downloaded file: {file_doc.name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Serve file for download
        import os
        if not os.path.exists(file_doc.file.path):
            raise Http404("File not found on disk")
        
        with open(file_doc.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=file_doc.mime_type or 'application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_doc.name}"'
            return response
        
    except Employee.DoesNotExist:
        raise Http404("Employee profile not found")
    except Exception as e:
        raise Http404(f"Error downloading file: {str(e)}")


@login_required
def view_file(request, file_id):
    """View file details"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check permissions
        if not (file_doc.uploaded_by == employee or 
                employee in file_doc.shared_with.all() or 
                file_doc.is_public):
            raise Http404("File not found")
        
        # Update access tracking
        file_doc.last_accessed = timezone.now()
        file_doc.save()
        
        # Log activity
        FileActivity.objects.create(
            document=file_doc,
            user=employee,
            action='view',
            details=f'Viewed file: {file_doc.name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Get file versions
        versions = FileVersion.objects.filter(document=file_doc)
        
        # Get sharing information
        shares = FileShare.objects.filter(document=file_doc)
        
        # Get recent activity
        activities = FileActivity.objects.filter(document=file_doc)[:10]
        
        # Add AI analysis
        ai_analysis = None
        try:
            analyzer, bot = create_free_ai_assistant()
            file_path = file_doc.get_file_path()
            if file_path and os.path.exists(file_path):
                ai_analysis = analyzer.analyze_file(file_path, file_doc.name)
        except Exception as e:
            # If analysis fails, create a basic structure
            ai_analysis = {
                'summary': f'Analysis unavailable: {str(e)}',
                'category': 'unknown',
                'key_topics': [],
                'has_text': False,
                'error': str(e)
            }
        
        context = {
            'file': file_doc,
            'employee': employee,
            'versions': versions,
            'shares': shares,
            'activities': activities,
            'can_edit': file_doc.uploaded_by == employee,
            'ai_analysis': ai_analysis,
        }
        
        return render(request, 'employee/file_detail.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


@login_required
def delete_file(request, file_id):
    """Delete a file"""
    if request.method == 'POST':
        try:
            employee = Employee.objects.get(user=request.user)
            file_doc = get_object_or_404(FileDocument, id=file_id, uploaded_by=employee)
            
            # Log activity before deletion
            FileActivity.objects.create(
                document=file_doc,
                user=employee,
                action='delete',
                details=f'Deleted file: {file_doc.name}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Delete the file
            file_name = file_doc.name
            file_doc.delete()
            
            # Update user's storage usage
            employee.update_storage_used()
            
            messages.success(request, f'File "{file_name}" deleted successfully.')
            return JsonResponse({
                'success': True, 
                'message': 'File deleted successfully',
                'storage_used': employee.get_storage_used_display(),
                'storage_quota': employee.get_storage_quota_display(),
                'storage_percentage': employee.get_storage_percentage()
            })
            
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Employee profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def share_file(request, file_id):
    """Share a file with other users via email"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id, uploaded_by=employee)
        
        if request.method == 'POST':
            form = FileShareForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                permission = form.cleaned_data['permission']
                message = form.cleaned_data.get('message', '')
                
                # Get the user and employee by email
                from django.contrib.auth.models import User
                user = User.objects.get(email=email)
                target_employee = Employee.objects.get(user=user)
                
                # Create or update share
                share, created = FileShare.objects.get_or_create(
                    document=file_doc,
                    shared_with=target_employee,
                    defaults={
                        'shared_by': employee,
                        'permission': permission
                    }
                )
                if not created:
                    share.permission = permission
                    share.save()
                
                # Log activity
                FileActivity.objects.create(
                    document=file_doc,
                    user=employee,
                    action='share',
                    details=f'Shared file with {target_employee.get_full_name()} ({email})',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # ===== AI WORKFLOW INTEGRATION =====
                try:
                    from .ai_workflow_service import get_ai_workflow_service
                    
                    ai_service = get_ai_workflow_service()
                    workflow_result = ai_service.handle_file_sharing(file_doc, employee, target_employee)
                    
                    if workflow_result['success']:
                        print(f"[AI WORKFLOWS] File sharing - Executed {workflow_result['executed_workflows']} workflows")
                    else:
                        print(f"[AI WORKFLOWS] File sharing error: {workflow_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    # Don't fail sharing if AI workflows fail
                    print(f"[AI WORKFLOWS] Failed to process file sharing workflows: {str(e)}")
                # ===== END AI WORKFLOW INTEGRATION =====
                
                messages.success(request, f'File shared with {target_employee.get_full_name()} ({email}).')
                return JsonResponse({'success': True, 'message': 'File shared successfully'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        
        form = FileShareForm()
        context = {
            'file': file_doc,
            'form': form,
            'employee': employee,
        }
        
        return render(request, 'employee/file_share.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


@login_required
def search_files(request):
    """Enhanced AI-powered search for files and folders"""
    try:
        employee = Employee.objects.get(user=request.user)
        form = FileSearchForm(request.GET)
        
        # Base queryset - user's files and shared files
        files = FileDocument.objects.filter(
            Q(uploaded_by=employee) | Q(shared_with=employee) | Q(is_public=True)
        ).select_related('ai_analysis').distinct()
        
        search_query = request.GET.get('query', '').strip()
        search_results = []
        ai_suggestions = []
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            file_type = form.cleaned_data.get('file_type')
            date_range = form.cleaned_data.get('date_range')
            tags = form.cleaned_data.get('tags')
            
            # Enhanced AI-powered search
            if query:
                search_results = _perform_ai_enhanced_search(files, query, employee)
                ai_suggestions = _generate_search_suggestions(query, employee)
            else:
                search_results = list(files)
            
            # Apply additional filters
            if file_type:
                search_results = [f for f in search_results if f.file_type == file_type]
            
            if date_range:
                now = timezone.now()
                if date_range == 'today':
                    search_results = [f for f in search_results if f.created_at.date() == now.date()]
                elif date_range == 'week':
                    search_results = [f for f in search_results if f.created_at >= now - timedelta(days=7)]
                elif date_range == 'month':
                    search_results = [f for f in search_results if f.created_at >= now - timedelta(days=30)]
                elif date_range == 'year':
                    search_results = [f for f in search_results if f.created_at >= now - timedelta(days=365)]
            
            if tags:
                tag_list = [tag.strip().lower() for tag in tags.split(',')]
                search_results = [f for f in search_results 
                                if any(tag in (f.tags or '').lower() for tag in tag_list)]
        
        # Convert to paginated results
        paginator = Paginator(search_results, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'files': page_obj,
            'form': form,
            'employee': employee,
            'search_performed': bool(search_query),
            'search_query': search_query,
            'ai_suggestions': ai_suggestions[:5],  # Limit to top 5 suggestions
            'total_results': len(search_results),
        }
        
        return render(request, 'employee/file_search.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


def _perform_ai_enhanced_search(files_queryset, query, employee):
    """Perform enhanced search using AI analysis data"""
    query_lower = query.lower()
    scored_results = []
    
    # Minimum score threshold for relevance
    MIN_RELEVANCE_SCORE = 20
    
    for file_obj in files_queryset:
        score = 0
        match_reasons = []
        
        # Basic filename and description matching (high weight)
        if query_lower in file_obj.name.lower():
            score += 100
            match_reasons.append(f"Filename contains '{query}'")
        
        if file_obj.description and query_lower in file_obj.description.lower():
            score += 80
            match_reasons.append(f"Description contains '{query}'")
        
        # Tags matching (high weight)
        if file_obj.tags and query_lower in file_obj.tags.lower():
            score += 90
            match_reasons.append(f"Tags contain '{query}'")
        
        # AI Analysis-based matching
        if hasattr(file_obj, 'ai_analysis') and file_obj.ai_analysis:
            analysis = file_obj.ai_analysis
            
            # Category matching (medium-high weight)
            if analysis.category and query_lower in analysis.category.lower():
                score += 70
                match_reasons.append(f"AI category: {analysis.category}")
            
            # Key topics matching (medium-high weight)
            if analysis.key_topics:
                for topic in analysis.key_topics:
                    if isinstance(topic, str) and query_lower in topic.lower():
                        score += 60
                        match_reasons.append(f"Key topic: {topic}")
            
            # Entities matching (medium weight)
            if analysis.entities:
                for entity in analysis.entities:
                    if isinstance(entity, str) and query_lower in entity.lower():
                        score += 50
                        match_reasons.append(f"Entity: {entity}")
                    elif isinstance(entity, dict) and 'text' in entity:
                        if query_lower in entity['text'].lower():
                            score += 50
                            match_reasons.append(f"Entity: {entity['text']}")
            
            # Suggested tags matching (medium weight)
            if analysis.suggested_tags:
                for tag in analysis.suggested_tags:
                    if isinstance(tag, str) and query_lower in tag.lower():
                        score += 45
                        match_reasons.append(f"AI suggested tag: {tag}")
            
            # Content type matching (lower weight)
            if analysis.content_type and query_lower in analysis.content_type.lower():
                score += 30
                match_reasons.append(f"Content type: {analysis.content_type}")
            
            # Language matching (lower weight)
            if analysis.language and query_lower in analysis.language.lower():
                score += 25
                match_reasons.append(f"Language: {analysis.language}")
            
            # Partial word matching in key topics and entities (only if main query didn't match)
            if score < MIN_RELEVANCE_SCORE:
                for topic in (analysis.key_topics or []):
                    if isinstance(topic, str):
                        topic_words = topic.lower().split()
                        if any(query_lower in word or word in query_lower for word in topic_words):
                            score += 25
                            match_reasons.append(f"Related topic: {topic}")
        
        # File type relevance (only exact matches)
        file_extension = file_obj.name.split('.')[-1].lower() if '.' in file_obj.name else ''
        if query_lower == file_extension or query_lower == file_obj.file_type.lower():
            score += 40
            match_reasons.append(f"File type: {file_obj.file_type}")
        
        # Only include files that meet minimum relevance threshold
        if score >= MIN_RELEVANCE_SCORE:
            # Small recency boost for relevant files
            days_old = (timezone.now() - file_obj.created_at).days
            if days_old < 7:
                score += 5
            elif days_old < 30:
                score += 2
            
            file_obj.search_score = score
            file_obj.match_reasons = match_reasons
            scored_results.append(file_obj)
    
    # Sort by score (highest first)
    scored_results.sort(key=lambda x: x.search_score, reverse=True)
    return scored_results


def _generate_search_suggestions(query, employee):
    """Generate AI-powered search suggestions"""
    suggestions = []
    query_lower = query.lower()
    
    # Get files with AI analysis
    analyzed_files = FileDocument.objects.filter(
        Q(uploaded_by=employee) | Q(shared_with=employee),
        ai_analysis__isnull=False
    ).select_related('ai_analysis')
    
    # Collect relevant topics, categories, and entities
    topics_set = set()
    categories_set = set()
    entities_set = set()
    
    for file_obj in analyzed_files:
        analysis = file_obj.ai_analysis
        
        # Add categories
        if analysis.category:
            categories_set.add(analysis.category)
        
        # Add key topics
        if analysis.key_topics:
            for topic in analysis.key_topics:
                if isinstance(topic, str):
                    topics_set.add(topic)
        
        # Add entities
        if analysis.entities:
            for entity in analysis.entities:
                if isinstance(entity, str):
                    entities_set.add(entity)
                elif isinstance(entity, dict) and 'text' in entity:
                    entities_set.add(entity['text'])
        
        # Add suggested tags
        if analysis.suggested_tags:
            for tag in analysis.suggested_tags:
                if isinstance(tag, str):
                    topics_set.add(tag)
    
    # Find suggestions that partially match the query
    def is_relevant(text, query_text):
        text_lower = text.lower()
        query_lower = query_text.lower()
        return (query_lower in text_lower or 
                text_lower in query_lower or 
                any(word in text_lower for word in query_lower.split()) or
                any(word in query_lower for word in text_lower.split()))
    
    # Add relevant categories
    for category in categories_set:
        if is_relevant(category, query) and category.lower() != query_lower:
            suggestions.append({
                'text': category,
                'type': 'category',
                'icon': 'fas fa-folder'
            })
    
    # Add relevant topics
    for topic in topics_set:
        if is_relevant(topic, query) and topic.lower() != query_lower:
            suggestions.append({
                'text': topic,
                'type': 'topic',
                'icon': 'fas fa-tag'
            })
    
    # Add relevant entities
    for entity in entities_set:
        if is_relevant(entity, query) and entity.lower() != query_lower:
            suggestions.append({
                'text': entity,
                'type': 'entity',
                'icon': 'fas fa-search'
            })
    
    # Remove duplicates and sort by relevance
    seen = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion['text'] not in seen:
            seen.add(suggestion['text'])
            unique_suggestions.append(suggestion)
    
    return unique_suggestions[:10]  # Return top 10 suggestions


@login_required
def file_activity(request):
    """View file activity logs"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Get activities for user's files
        activities = FileActivity.objects.filter(
            Q(user=employee) | Q(document__uploaded_by=employee)
        ).select_related('document', 'user')
        
        # Pagination
        paginator = Paginator(activities, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'activities': page_obj,
            'employee': employee,
        }
        
        return render(request, 'employee/file_activity.html', context)
    
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


@login_required
def search_employees_by_email(request):
    """API endpoint to search employees by email for sharing"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        current_employee = Employee.objects.get(user=request.user)
        
        # Search by email, first name, last name
        from django.contrib.auth.models import User
        users = User.objects.filter(
            Q(email__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=current_employee.user.id)[:10]  # Limit to 10 results
        
        results = []
        for user in users:
            try:
                employee = Employee.objects.get(user=user)
                results.append({
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}".strip(),
                    'department': employee.department,
                    'display': f"{user.first_name} {user.last_name} ({user.email})"
                })
            except Employee.DoesNotExist:
                continue
        
        return JsonResponse({'results': results})
    
    except Employee.DoesNotExist:
        return JsonResponse({'results': []})
    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})


@login_required
def ai_chat(request):
    """AI Assistant chat endpoint with conversation memory"""
    if request.method == 'POST':
        try:
            employee = Employee.objects.get(user=request.user)
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            
            if not query:
                return JsonResponse({'error': 'No query provided'})
            
            # Get or create conversation session
            session_key = f'ai_chat_{request.user.id}'
            if session_key not in request.session:
                request.session[session_key] = {
                    'conversation_history': [],
                    'last_search_results': [],
                    'awaiting_clarification': False,
                    'clarification_context': None,
                    'user_context': {}
                }
            
            # Get user's files
            user_files = FileDocument.objects.filter(
                Q(uploaded_by=employee) | Q(shared_with=employee)
            ).distinct()
            
            # Create AI assistant
            analyzer, bot = create_free_ai_assistant()
            
            # Prepare file analyses for the bot
            file_analyses = []
            for file_doc in user_files:
                try:
                    analysis = analyzer.analyze_file(file_doc.file.path, file_doc.name)
                    analysis['file_id'] = str(file_doc.id)
                    file_analyses.append(analysis)
                except Exception as e:
                    continue
            
            # Load analyses into bot
            bot.load_analyses(file_analyses)
            
            # Restore conversation state
            session_data = request.session[session_key]
            bot.conversation_history = session_data.get('conversation_history', [])
            bot.last_search_results = session_data.get('last_search_results', [])
            bot.awaiting_clarification = session_data.get('awaiting_clarification', False)
            bot.clarification_context = session_data.get('clarification_context', None)
            bot.user_context = session_data.get('user_context', {})
            
            # Process query
            response = bot.process_query(query)
            
            # Save conversation state (ensure all data is JSON serializable)
            conversation_history = []
            for item in bot.conversation_history[-20:]:  # Keep last 20 exchanges
                if isinstance(item.get('timestamp'), datetime):
                    item = item.copy()
                    item['timestamp'] = item['timestamp'].isoformat()
                conversation_history.append(item)
            
            # Ensure search results don't contain datetime objects
            last_search_results = []
            for result in bot.last_search_results:
                if isinstance(result.get('analysis_date'), str) or result.get('analysis_date') is None:
                    last_search_results.append(result)
                else:
                    result_copy = result.copy()
                    if 'analysis_date' in result_copy:
                        result_copy['analysis_date'] = str(result_copy['analysis_date'])
                    last_search_results.append(result_copy)
            
            request.session[session_key] = {
                'conversation_history': conversation_history,
                'last_search_results': last_search_results,
                'awaiting_clarification': bot.awaiting_clarification,
                'clarification_context': bot.clarification_context,
                'user_context': bot.user_context
            }
            request.session.modified = True
            
            return JsonResponse({
                'response': response,
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'conversation_context': {
                    'awaiting_clarification': bot.awaiting_clarification,
                    'has_results': len(bot.last_search_results) > 0
                }
            })
            
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee profile not found'})
        except Exception as e:
            return JsonResponse({'error': f'Error processing query: {str(e)}'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def analyze_file_ai(request, file_id):
    """Get AI analysis for a specific file"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check permissions
        if not (file_doc.uploaded_by == employee or 
                employee in file_doc.shared_with.all() or 
                file_doc.is_public):
            return JsonResponse({'error': 'Access denied'})
        
        # Create AI assistant
        analyzer, _ = create_free_ai_assistant()
        
        # Analyze the file
        analysis = analyzer.analyze_file(file_doc.file.path, file_doc.name)
        
        return JsonResponse({
            'analysis': analysis,
            'file_id': str(file_doc.id),
            'file_name': file_doc.name
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'})
    except Exception as e:
        return JsonResponse({'error': f'Error analyzing file: {str(e)}'})


@login_required
def ai_assistant_page(request):
    """AI Assistant main page"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Get user's files for context
        user_files = FileDocument.objects.filter(
            Q(uploaded_by=employee) | Q(shared_with=employee)
        ).distinct()
        
        context = {
            'employee': employee,
            'file_count': user_files.count(),
            'recent_files': user_files[:5]
        }
        
        return render(request, 'employee/ai_assistant.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


@login_required
@require_http_methods(["POST"])
def move_file(request):
    """Move a file to a different folder via drag and drop"""
    print(f"=== MOVE FILE VIEW CALLED ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User: {request.user}")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    print(f"Request body: {request.body}")
    print(f"Request POST: {request.POST}")
    
    try:
        employee = Employee.objects.get(user=request.user)
        print(f"Employee found: {employee}")
        
        # Parse JSON data from request body
        try:
            data = json.loads(request.body)
            print(f"Parsed JSON data: {data}")
        except json.JSONDecodeError as json_error:
            print(f"JSON decode error: {json_error}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        
        file_id = data.get('file_id')
        target_folder_id = data.get('target_folder_id')
        
        # Debug logging
        print(f"Move file request: file_id={file_id}, target_folder_id={target_folder_id}")
        
        if not file_id:
            return JsonResponse({
                'success': False,
                'message': 'File ID is required'
            })
        
        # Get the file
        try:
            file_obj = FileDocument.objects.get(
                id=file_id,
                uploaded_by=employee  # Only allow moving own files
            )
            print(f"Found file: {file_obj.name}")
        except FileDocument.DoesNotExist:
            print(f"File not found: {file_id}")
            return JsonResponse({
                'success': False,
                'message': 'File not found or access denied'
            })
        
        # Get target folder if specified
        target_folder = None
        if target_folder_id:
            try:
                target_folder = FileFolder.objects.get(
                    id=target_folder_id,
                    created_by=employee  # Only allow moving to own folders
                )
                print(f"Found target folder: {target_folder.name}")
            except FileFolder.DoesNotExist:
                print(f"Folder not found: {target_folder_id}")
                return JsonResponse({
                    'success': False,
                    'message': 'Target folder not found or access denied'
                })
        else:
            print("Moving to root folder")
        
        # Check if file is already in the target folder
        if file_obj.folder == target_folder:
            print("File already in target folder")
            return JsonResponse({
                'success': False,
                'message': 'File is already in this folder'
            })
        
        # Move the file
        old_folder_name = file_obj.folder.name if file_obj.folder else 'Root'
        new_folder_name = target_folder.name if target_folder else 'Root'
        
        print(f"Moving file from '{old_folder_name}' to '{new_folder_name}'")
        
        file_obj.folder = target_folder
        file_obj.save()
        
        print("File moved successfully")
        
        # Log the activity
        try:
            FileActivity.objects.create(
                document=file_obj,
                user=employee,
                action='move',
                details=f'Moved from "{old_folder_name}" to "{new_folder_name}"'
            )
            print("Activity logged")
        except Exception as activity_error:
            print(f"Failed to log activity: {activity_error}")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully moved "{file_obj.name}" to "{new_folder_name}"'
        })
        
    except Employee.DoesNotExist:
        print("Employee profile not found")
        return JsonResponse({
            'success': False,
            'message': 'Employee profile not found'
        })
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def unshare_file(request, file_id, share_id):
    """Remove a file share"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check if user can manage this file (owner or admin)
        if file_doc.uploaded_by != employee and not employee.is_admin():
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        share = get_object_or_404(FileShare, id=share_id, document=file_doc)
        shared_with_name = share.shared_with.get_full_name()
        share.delete()
        
        # Log the activity
        FileActivity.objects.create(
            document=file_doc,
            user=employee,
            action='unshare',
            details=f'removed sharing with {shared_with_name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'File sharing removed for {shared_with_name}')
        return JsonResponse({'success': True})
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_file_share(request, file_id, share_id):
    """Update file share permission"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check if user can manage this file (owner or admin)
        if file_doc.uploaded_by != employee and not employee.is_admin():
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        share = get_object_or_404(FileShare, id=share_id, document=file_doc)
        new_permission = request.POST.get('permission')
        
        if new_permission not in ['view', 'edit', 'full']:
            return JsonResponse({'error': 'Invalid permission'}, status=400)
        
        old_permission = share.get_permission_display()
        share.permission = new_permission
        share.save()
        
        # Log the activity
        FileActivity.objects.create(
            document=file_doc,
            user=employee,
            action='share_update',
            details=f'changed {share.shared_with.get_full_name()} permission from {old_permission} to {share.get_permission_display()}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'Permission updated for {share.shared_with.get_full_name()}')
        return JsonResponse({'success': True})
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def transfer_file_ownership(request, file_id):
    """Transfer file ownership to another user"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Only the current owner can transfer ownership
        if file_doc.uploaded_by != employee:
            return JsonResponse({'error': 'Only the file owner can transfer ownership'}, status=403)
        
        new_owner_id = request.POST.get('new_owner_id')
        new_owner = get_object_or_404(Employee, id=new_owner_id)
        
        old_owner_name = employee.get_full_name()
        file_doc.uploaded_by = new_owner
        file_doc.save()
        
        # Log the activity
        FileActivity.objects.create(
            document=file_doc,
            user=employee,
            action='transfer_ownership',
            details=f'transferred ownership from {old_owner_name} to {new_owner.get_full_name()}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'File ownership transferred to {new_owner.get_full_name()}')
        return JsonResponse({'success': True})
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_file_details(request, file_id):
    """Get detailed file information including sharing data"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id)
        
        # Check if user has access to this file
        has_access = (
            file_doc.uploaded_by == employee or
            file_doc.shares.filter(shared_with=employee).exists() or
            employee.is_admin()
        )
        
        if not has_access:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get file shares if user is owner
        shares_data = []
        if file_doc.uploaded_by == employee:
            shares = file_doc.shares.all().select_related('shared_with')
            shares_data = [{
                'id': str(share.id),
                'shared_with_name': share.shared_with.get_full_name(),
                'shared_with_department': share.shared_with.department,
                'permission': share.permission,
                'created_at': share.created_at.strftime('%b %d, %Y')
            } for share in shares]
        
        file_data = {
            'id': str(file_doc.id),
            'name': file_doc.name,
            'size': file_doc.get_file_size_display(),
            'content_type': file_doc.content_type,
            'file_type': file_doc.file_type,
            'owner_name': file_doc.uploaded_by.get_full_name(),
            'is_owner': file_doc.uploaded_by == employee,
            'created_at': file_doc.created_at.strftime('%b %d, %Y %I:%M %p'),
            'updated_at': file_doc.updated_at.strftime('%b %d, %Y %I:%M %p'),
        }
        
        return JsonResponse({
            'success': True,
            'file': file_data,
            'shares': shares_data
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def storage_management(request):
    """Storage management view for administrators using manual allocation"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Only admins can access storage management
        if not employee.is_admin():
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('file_manager')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'update_quotas':
                # Update all user quotas based on current storage allocation
                from .models import StorageAllocation, StorageManager
                allocation_gb = StorageAllocation.get_current_allocation()
                user_quota = StorageManager.calculate_user_quota()
                
                # Update all user quotas
                updated_count = Employee.objects.filter(is_active=True).update(storage_quota=user_quota)
                messages.success(request, 
                    f'Updated quotas for {updated_count} users to {Employee._format_bytes(user_quota)} each.')
                
            elif action == 'recalculate_usage':
                # Recalculate storage usage for all users
                updated_count = 0
                for emp in Employee.objects.filter(is_active=True):
                    emp.update_storage_used()
                    updated_count += 1
                messages.success(request, f'Recalculated storage usage for {updated_count} users.')
        
        # Get storage statistics using manual allocation
        from .models import StorageAllocation, StorageManager
        allocation_gb = StorageAllocation.get_current_allocation()
        
        # Calculate statistics based on manual allocation
        active_users = Employee.objects.filter(is_active=True).count()
        total_user_storage = Employee.objects.filter(is_active=True).aggregate(
            total=Sum('storage_used')
        )['total'] or 0
        
        total_files = FileDocument.objects.count()
        user_quota = StorageManager.calculate_user_quota()
        
        storage_stats = {
            'allocation': {
                'total_allocated': allocation_gb * (1024 ** 3),  # Convert to bytes
                'total_allocated_display': f"{allocation_gb} GB",
                'quota_per_user': user_quota,
                'quota_per_user_display': Employee._format_bytes(user_quota),
            },
            'active_users': active_users,
            'total_files': total_files,
            'total_user_storage': total_user_storage,
            'total_user_storage_display': Employee._format_bytes(total_user_storage),
        }
        
        # Get top storage users
        top_users = Employee.objects.filter(is_active=True).exclude(
            storage_used__isnull=True
        ).order_by('-storage_used')[:10]
        
        # Get users over quota
        over_quota_users = Employee.objects.filter(
            is_active=True,
            storage_used__gt=F('storage_quota')
        ).exclude(
            storage_quota__isnull=True
        )
        
        context = {
            'storage_stats': storage_stats,
            'top_users': top_users,
            'over_quota_users': over_quota_users,
            'employee': employee,
            'allocation_gb': allocation_gb,
        }
        
        return render(request, 'employee/storage_management.html', context)
        
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('employee_dashboard')


@login_required
def get_storage_info(request):
    """API endpoint to get current user's storage information"""
    try:
        employee = Employee.objects.get(user=request.user)
        
        # Update quota if not set
        if employee.storage_quota is None:
            from .models import StorageManager
            employee.storage_quota = StorageManager.calculate_user_quota()
            employee.save()
        
        return JsonResponse({
            'success': True,
            'storage_used': employee.storage_used,
            'storage_quota': employee.storage_quota,
            'storage_used_display': employee.get_storage_used_display(),
            'storage_quota_display': employee.get_storage_quota_display(),
            'storage_percentage': employee.get_storage_percentage(),
            'available_storage': employee.get_available_storage(),
            'available_storage_display': Employee._format_bytes(employee.get_available_storage())
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee profile not found'}, status=401)


@login_required
@require_http_methods(["POST"])
def trigger_ai_analysis(request, file_id):
    """Trigger AI analysis for a file to test enhanced search"""
    try:
        employee = Employee.objects.get(user=request.user)
        file_doc = get_object_or_404(FileDocument, id=file_id, uploaded_by=employee)
        
        # Create or update AI analysis with sample data for testing
        analysis, created = AIFileAnalysis.objects.get_or_create(
            document=file_doc,
            defaults={
                'analysis_completed': True,
                'analysis_completed_at': timezone.now(),
                'content_type': 'document',
                'language': 'en',
                'category': 'Technical Document',
                'key_topics': ['artificial intelligence', 'machine learning', 'technology', 'research'],
                'entities': ['AI', 'neural networks', 'algorithms', 'data science'],
                'sentiment_score': 0.7,
                'sentiment_label': 'positive',
                'quality_score': 4.2,
                'suggested_tags': ['AI', 'tech', 'research', 'documentation'],
                'ai_recommendations': [
                    {'title': 'Content Quality', 'description': 'High-quality technical content detected'},
                    {'title': 'Categorization', 'description': 'Automatically categorized as Technical Document'}
                ]
            }
        )
        
        if not created:
            # Update existing analysis with enhanced data
            analysis.analysis_completed = True
            analysis.analysis_completed_at = timezone.now()
            analysis.key_topics = ['artificial intelligence', 'machine learning', 'technology', 'research']
            analysis.entities = ['AI', 'neural networks', 'algorithms', 'data science']
            analysis.category = 'Technical Document'
            analysis.quality_score = 4.2
            analysis.suggested_tags = ['AI', 'tech', 'research', 'documentation']
            analysis.save()
        
        return JsonResponse({
            'success': True,
            'message': 'AI analysis completed successfully',
            'analysis_id': str(analysis.id)
        })
        
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

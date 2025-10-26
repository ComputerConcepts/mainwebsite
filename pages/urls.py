from django.contrib import admin
from django.urls import include, path
from . import views
from . import views_boards
from . import views_admin
from . import views_files
from . import views_ai
from . import views_chat
from . import views_onboarding_hr
from . import views_onboarding_portal
from . import views_tax


urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('email', views.email, name='email'),
    path('contact', views.contact, name='contact'),
    path('forgot/password', views.forgotPassword, name='forgotPassword'),
    path('reset/password/<uidb64>/<token>/', views.reset, name='reset'),
    path('sitemap', views.sitemap, name='sitemap'),
    path('events', views.events, name='events'),
    path('admin/events', views.adminEvents, name = 'adminEvents'),
    path('admin/events/create', views.adminEventsCreate, name = 'adminEventsCreate'),
    path('admin/events/image/add/<uuid:event_id>', views.add_image, name = 'add_image'),
    path('admin/events/status/change/<uuid:event_id>', views.change_event, name = 'change_event'),
    path('admin/events/invoices/<uuid:event_id>', views.invoices, name = "invoices"),
    path('buy-tickets/<uuid:event_id>/', views.buy_tickets, name='buy_tickets'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('tickets/show', views.show_tickets, name='show_tickets'),
    path('tickets/verify', views.verify_tickets, name='verify_tickets'),
    path('login', views.login_view, name='login'),
    path('tickets/verify/success/<uuid:invoice_id>/<uuid:ticket_id>/', views.verifyTicketSuccess, name='verifyTicketSuccess'),
    path('verify/failure/<uuid:invoice_id>/<uuid:ticket_id>/', views.verifyTicketFailure, name='verifyTicketFailure'),
    path('payment/confirmation/<uuid:invoice_id>', views.payment_success, name='payment_success'),
    path('payment/<uuid:invoice_id>/', views.payment_page, name='payment_page'),
    path('careers/', views.careers, name='careers'),
    
    # Employee Portal URLs
    path('employee/login/', views.employee_login, name='employee_login'),
    path('employee/logout/', views.employee_logout, name='employee_logout'),
    # Registration removed - using password reset flow for new users
    path('employee/verify-email/<uuid:employee_id>/', views.employee_verify_email, name='employee_verify_email'),
    path('employee/confirm-email/<uuid:employee_id>/<str:token>/', views.employee_email_confirm, name='employee_email_confirm'),
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/profile/', views.employee_profile, name='employee_profile'),
    path('employee/events/', views.employee_events, name='employee_events'),
    path('employee/events/<uuid:event_id>/', views.employee_event_detail, name='employee_event_detail'),
    path('employee/test-email/', views.test_email, name='test_email'),
    path('employee/help/', views.employee_help, name='employee_help'),
    path('employee/careers/', views.admin_careers, name='admin_careers'),
    path('employee/careers/<uuid:career_id>/', views.admin_career_detail, name='admin_career_detail'),
    path('employee/jobs/', views.admin_jobs, name='admin_jobs'),
    path('employee/jobs/create/', views.admin_job_create, name='admin_job_create'),
    path('employee/jobs/<uuid:job_id>/', views.admin_job_detail, name='admin_job_detail'),
    path('employee/jobs/<uuid:job_id>/edit/', views.admin_job_edit, name='admin_job_edit'),
    path('employee/jobs/<uuid:job_id>/delete/', views.admin_job_delete, name='admin_job_delete'),
    path('employee/jobs/<uuid:job_id>/toggle-status/', views.admin_job_toggle_status, name='admin_job_toggle_status'),
    path('employee/applications/<uuid:application_id>/', views.admin_application_detail, name='admin_application_detail'),
    path('employee/applications/<uuid:application_id>/update-status/', views.admin_application_update_status, name='admin_application_update_status'),
    path('careers/<uuid:job_id>/', views.career_apply, name='career_apply'),
    
    # Storage Management URLs for Employee Portal
    path('employee/storage/overview/', views.admin_storage_overview, name='admin_storage_overview'),
    path('employee/storage/update-quotas/', views.admin_update_storage_quotas, name='admin_update_storage_quotas'),
    path('employee/storage/set-quota/<uuid:user_id>/', views.admin_set_user_quota, name='admin_set_user_quota'),
    path('employee/storage/set-allocation/', views.admin_set_storage_allocation, name='admin_set_storage_allocation'),
    path('employee/storage/my-storage/', views.user_storage_details, name='user_storage_details'),
    
    # Admin Management URLs
    path('employee/admin/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('employee/admin/users/', views_admin.user_management, name='user_management'),
    path('employee/admin/users/<uuid:user_id>/', views_admin.user_detail, name='user_detail'),
    path('employee/admin/users/create/', views_admin.create_user, name='create_user'),
    path('employee/admin/users/<uuid:user_id>/toggle-status/', views_admin.toggle_user_status, name='toggle_user_status'),
    path('employee/admin/users/<uuid:user_id>/reset-password/', views_admin.reset_user_password, name='reset_user_password'),
    path('employee/admin/users/<uuid:user_id>/verify-email/', views_admin.verify_user_email, name='verify_user_email'),
    path('employee/admin/users/<uuid:user_id>/unverify-email/', views_admin.unverify_user_email, name='unverify_user_email'),
    path('employee/admin/users/<uuid:user_id>/send-verification/', views_admin.send_verification_email, name='send_verification_email'),
    path('employee/admin/bulk-action/', views_admin.bulk_action, name='bulk_action'),
    
    # Project Board URLs
    path('employee/boards/', views_boards.project_boards, name='project_boards'),
    path('employee/boards/create/', views_boards.create_board, name='create_board'),
    path('employee/boards/<uuid:board_id>/', views_boards.board_detail, name='board_detail'),
    path('employee/boards/<uuid:board_id>/delete/', views_boards.delete_board, name='delete_board'),
    path('employee/boards/<uuid:board_id>/share/', views_boards.share_board, name='share_board'),
    path('employee/boards/<uuid:board_id>/unshare/<uuid:share_id>/', views_boards.unshare_board, name='unshare_board'),
    path('employee/boards/<uuid:board_id>/transfer-ownership/', views_boards.transfer_board_ownership, name='transfer_board_ownership'),
    path('employee/boards/<uuid:board_id>/update-share/<uuid:share_id>/', views_boards.update_board_share, name='update_board_share'),
    path('employee/boards/<uuid:board_id>/activity/', views_boards.board_activity, name='board_activity'),
    path('employee/boards/activity/', views_boards.board_activity_list, name='board_activity_list'),
    path('api/boards/<uuid:board_id>/lists/create/', views_boards.create_list, name='create_list'),
    path('api/boards/<uuid:board_id>/members/', views_boards.get_board_members, name='get_board_members'),
    path('api/boards/<uuid:board_id>/members/add/', views_boards.add_board_member, name='add_board_member'),
    path('api/boards/<uuid:board_id>/members/remove/', views_boards.remove_board_member, name='remove_board_member'),
    path('api/employees/search/', views_boards.search_employees, name='search_employees'),
    path('api/employees/search-for-sharing/', views_boards.search_employees_for_board_sharing, name='search_employees_for_board_sharing'),
    path('api/lists/<uuid:list_id>/cards/create/', views_boards.create_card, name='create_card'),
    path('api/cards/<uuid:card_id>/', views_boards.card_detail, name='card_detail'),
    path('api/cards/<uuid:card_id>/update/', views_boards.update_card, name='update_card'),
    path('api/cards/<uuid:card_id>/comments/', views_boards.add_card_comment, name='add_card_comment'),
    path('api/cards/move/', views_boards.move_card, name='move_card'),
    
    # File Management URLs
    path('employee/files/', views_files.file_manager, name='file_manager'),
    path('employee/files/upload/', views_files.upload_file, name='upload_file'),
    path('employee/files/create-folder/', views_files.create_folder, name='create_folder'),
    path('employee/files/move/', views_files.move_file, name='move_file'),
    path('employee/files/download/<uuid:file_id>/', views_files.download_file, name='download_file'),
    path('employee/files/serve/<uuid:file_id>/', views_files.serve_file, name='serve_file'),
    path('employee/files/test/<uuid:file_id>/', views_files.test_file_serve, name='test_file_serve'),
    path('employee/files/view/<uuid:file_id>/', views_files.view_file, name='view_file'),
    path('employee/files/delete/<uuid:file_id>/', views_files.delete_file, name='delete_file'),
    path('employee/files/share/<uuid:file_id>/', views_files.share_file, name='share_file'),
    path('employee/files/unshare/<uuid:file_id>/<uuid:share_id>/', views_files.unshare_file, name='unshare_file'),
    path('employee/files/update-share/<uuid:file_id>/<uuid:share_id>/', views_files.update_file_share, name='update_file_share'),
    path('employee/files/transfer-ownership/<uuid:file_id>/', views_files.transfer_file_ownership, name='transfer_file_ownership'),
    path('employee/files/storage-management/', views_files.storage_management, name='storage_management'),
    path('api/files/<uuid:file_id>/details/', views_files.get_file_details, name='get_file_details'),
    path('api/storage/info/', views_files.get_storage_info, name='get_storage_info'),
    path('employee/files/search/', views_files.search_files, name='search_files'),
    path('employee/files/activity/', views_files.file_activity, name='file_activity'),
    path('api/files/<uuid:file_id>/trigger-analysis/', views_files.trigger_ai_analysis, name='trigger_ai_analysis'),
    path('api/employees/search-email/', views_files.search_employees_by_email, name='search_employees_by_email'),
    path('api/files/<uuid:file_id>/details/', views_files.get_file_details, name='get_file_details'),
    
    # AI Assistant URLs
    path('employee/ai-assistant/', views_files.ai_assistant_page, name='ai_assistant'),
    path('api/ai/chat/', views_files.ai_chat, name='ai_chat'),
    path('api/ai/analyze/<uuid:file_id>/', views_files.analyze_file_ai, name='analyze_file_ai'),
    path('api/files/<uuid:file_id>/analysis/', views_files.get_file_analysis, name='get_file_analysis'),
    
    # AI Workflow URLs
    path('employee/ai/', views_ai.ai_dashboard, name='ai_dashboard'),
    path('employee/ai/notifications/', views_ai.ai_notifications, name='ai_notifications'),
    path('employee/ai/notifications/<uuid:notification_id>/read/', views_ai.mark_notification_read, name='mark_notification_read'),
    path('employee/ai/notifications/read-all/', views_ai.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('employee/ai/workflows/', views_ai.ai_workflows, name='ai_workflows'),
    path('employee/ai/workflows/<uuid:rule_id>/toggle/', views_ai.toggle_workflow_rule, name='toggle_workflow_rule'),
    path('employee/ai/analytics/', views_ai.ai_analytics, name='ai_analytics'),
    path('employee/ai/settings/', views_ai.ai_settings, name='ai_settings'),
    path('employee/ai/analysis/<int:analysis_id>/', views_ai.file_analysis_detail, name='file_analysis_detail'),
    path('employee/ai/execution/<uuid:execution_id>/', views_ai.ai_workflow_execution_detail, name='ai_workflow_execution_detail'),
    path('employee/ai/queue/', views_ai.ai_queue_dashboard, name='ai_queue_dashboard'),
    path('api/ai/analyze-file/<uuid:file_id>/', views_ai.trigger_manual_analysis, name='trigger_manual_analysis'),
    path('api/ai/analysis-status/<int:analysis_id>/', views_ai.check_analysis_status, name='check_analysis_status'),
    path('api/ai/retry-analysis/<int:analysis_id>/', views_ai.retry_failed_analysis, name='retry_failed_analysis'),
    
    # Storage Management Admin URLs
    path('admin/storage/update-quota/<int:user_id>/', views_admin.update_user_quota, name='admin_update_user_quota'),
    path('admin/storage/recalculate/<int:user_id>/', views_admin.recalculate_storage, name='admin_recalculate_storage'),
    path('admin/storage/view-files/<int:user_id>/', views_admin.view_user_files, name='admin_view_user_files'),
    path('admin/storage/bulk-update/', views_admin.bulk_update_quotas, name='admin_bulk_update_quotas'),
    path('admin/storage/overview/', views_admin.storage_overview, name='admin_storage_overview'),
    
    # Chat URLs
    path('employee/chat/', views_chat.chat_dashboard, name='chat_dashboard'),
    path('employee/chat/channel/<uuid:channel_id>/', views_chat.chat_channel, name='chat_channel'),
    path('employee/chat/dm/<uuid:recipient_id>/', views_chat.chat_direct_message, name='chat_direct_message'),
    path('employee/chat/create/', views_chat.create_channel, name='create_channel'),
    path('employee/chat/send/', views_chat.send_message, name='send_message'),
    path('employee/chat/send-ajax/', views_chat.send_message_ajax, name='send_message_ajax'),
    path('employee/chat/poll/<uuid:channel_id>/', views_chat.poll_messages, name='poll_messages'),
    path('employee/chat/notifications/', views_chat.chat_notifications, name='chat_notifications'),
    path('employee/chat/notifications/<uuid:notification_id>/read/', views_chat.mark_notification_read, name='mark_notification_read'),
    
    # Chat Integration URLs
    path('employee/chat/api/boards/', views_chat.get_user_boards, name='get_user_boards'),
    path('employee/chat/api/files/', views_chat.get_user_files, name='get_user_files'),
    path('employee/chat/channel/<uuid:channel_id>/share-board/<uuid:board_id>/', views_chat.share_board_to_channel, name='share_board_to_channel'),
    path('employee/chat/channel/<uuid:channel_id>/share-file/<uuid:file_id>/', views_chat.share_file_to_channel, name='share_file_to_channel'),
    path('employee/chat/channel/<uuid:channel_id>/boards/', views_chat.channel_boards, name='channel_boards'),
    path('employee/chat/channel/<uuid:channel_id>/files/', views_chat.channel_files, name='channel_files'),
    path('employee/chat/download/<uuid:file_share_id>/', views_chat.download_shared_file, name='download_shared_file'),
    
    # Chat member management
    path('api/channels/<uuid:channel_id>/invite/', views_chat.invite_channel_members, name='invite_channel_members'),
    path('api/channels/<uuid:channel_id>/settings/', views_chat.update_channel_settings, name='update_channel_settings'),
    path('api/channels/<uuid:channel_id>/delete/', views_chat.delete_channel, name='delete_channel'),
    
    # HR Onboarding System URLs
    path('employee/hr/onboarding/', views_onboarding_hr.hr_onboarding_dashboard, name='hr_onboarding_dashboard'),
    path('employee/hr/onboarding/forms/create/', views_onboarding_hr.create_onboarding_form, name='create_onboarding_form'),
    path('employee/hr/onboarding/forms/<uuid:form_id>/edit/', views_onboarding_hr.edit_onboarding_form, name='edit_onboarding_form'),
    path('employee/hr/onboarding/invite/', views_onboarding_hr.send_onboarding_invitation, name='send_onboarding_invitation'),
    path('employee/hr/onboarding/submissions/', views_onboarding_hr.onboarding_submissions, name='onboarding_submissions'),
    path('employee/hr/onboarding/submissions/<uuid:submission_id>/', views_onboarding_hr.submission_detail, name='hr_submission_detail'),
    path(
        'employee/hr/onboarding/submissions/<uuid:submission_id>/download/<slug:field_name>/',
        views_onboarding_hr.download_submission_file,
        name='download_submission_file',
    ),
    path('employee/hr/onboarding/submissions/<uuid:submission_id>/download/', views_onboarding_hr.download_combined_pdf, name='download_combined_pdf'),

    # Prospective Employee Onboarding Portal URLs
    path('onboarding/', views_onboarding_portal.onboarding_info, name='onboarding_info'),
    path('onboarding/login/', views_onboarding_portal.onboarding_login, name='onboarding_login'),
    path('onboarding/dashboard/', views_onboarding_portal.onboarding_dashboard, name='onboarding_dashboard'),
    path('onboarding/form/<uuid:invitation_id>/', views_onboarding_portal.onboarding_form, name='onboarding_form'),
    path('onboarding/status/<uuid:submission_id>/', views_onboarding_portal.onboarding_status, name='onboarding_status'),
    path('onboarding/logout/', views_onboarding_portal.onboarding_logout, name='onboarding_logout'),
    path('onboarding/api/form/<uuid:form_id>/field/<str:field_name>/options/', views_onboarding_portal.form_field_options, name='form_field_options'),
    
    # =============================================================================
    # TAX PREPARATION SYSTEM URLs
    # =============================================================================
    
    # Tax Admin URLs (Staff/Employee Access)
    path('employee/tax/', views_tax.tax_admin_dashboard, name='tax_admin_dashboard'),
    path('employee/tax/templates/', views_tax.tax_form_templates, name='tax_form_templates'),
    path('employee/tax/templates/create/', views_tax.create_tax_form_template, name='create_tax_form_template'),
    path('employee/tax/templates/<uuid:template_id>/edit/', views_tax.edit_tax_form_template, name='edit_tax_form_template'),
    path('employee/tax/templates/<uuid:template_id>/add-field/', views_tax.add_form_field, name='add_tax_form_field'),
    path('employee/tax/clients/', views_tax.manage_clients, name='manage_tax_clients'),
    path('employee/tax/clients/create/', views_tax.create_client, name='create_tax_client'),
    path('employee/tax/clients/<uuid:client_id>/', views_tax.client_detail, name='tax_client_detail'),
    path('employee/tax/clients/<uuid:client_id>/waiver/', views_tax.client_waiver, name='client_waiver'),
    path('employee/tax/clients/<uuid:client_id>/assign/', views_tax.assign_forms, name='assign_tax_forms'),
    path('employee/tax/clients/<uuid:client_id>/forms/', views_tax.client_forms, name='client_tax_forms'),
    path('employee/tax/clients/<uuid:client_id>/send-reminder/', views_tax.send_client_reminder, name='send_client_reminder'),
    path('employee/tax/clients/<uuid:client_id>/send-login-help/', views_tax.send_login_help, name='send_login_help'),
    path('employee/tax/clients/<uuid:client_id>/deactivate/', views_tax.deactivate_client, name='deactivate_client'),
    path('employee/tax/forms/<uuid:assignment_id>/fill/', views_tax.employee_fill_form, name='employee_fill_form'),
    path('employee/tax/assignments/<uuid:assignment_id>/view/', views_tax.view_tax_assignment, name='view_tax_assignment'),
    path('employee/tax/assignments/<uuid:assignment_id>/pdf/', views_tax.export_tax_assignment_pdf, name='export_tax_assignment_pdf'),
    
    # Tax Client Portal URLs (Public Access)
    path('tax/', views_tax.tax_client_login, name='tax_client_login'),
    path('tax/login/', views_tax.tax_client_login, name='tax_client_login'),
    path('tax/logout/', views_tax.tax_client_logout, name='tax_client_logout'),
    path('tax/debug/', views_tax.tax_client_debug, name='tax_client_debug'),  # Debug view
    path('tax/dashboard/', views_tax.tax_client_dashboard, name='tax_client_dashboard'),
    path('tax/waiver/', views_tax.tax_client_waiver, name='tax_client_waiver'),
    path('tax/form/<uuid:assignment_id>/', views_tax.tax_form_fill, name='tax_form_fill'),
    path('tax/review/<uuid:submission_id>/', views_tax.tax_client_review_form, name='tax_client_review_form'),
]

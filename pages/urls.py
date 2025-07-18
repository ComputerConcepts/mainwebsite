from django.contrib import admin
from django.urls import include, path
from . import views
from . import views_boards
from . import views_admin


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
    path('employee/applications/<uuid:application_id>/', views.admin_application_detail, name='admin_application_detail'),
    path('employee/applications/<uuid:application_id>/update-status/', views.admin_application_update_status, name='admin_application_update_status'),
    path('careers/<uuid:job_id>/', views.career_apply, name='career_apply'),
    
    # Admin Management URLs
    path('employee/admin/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('employee/admin/users/', views_admin.user_management, name='user_management'),
    path('employee/admin/users/<uuid:user_id>/', views_admin.user_detail, name='user_detail'),
    path('employee/admin/users/create/', views_admin.create_user, name='create_user'),
    path('employee/admin/users/<uuid:user_id>/toggle-status/', views_admin.toggle_user_status, name='toggle_user_status'),
    path('employee/admin/users/<uuid:user_id>/reset-password/', views_admin.reset_user_password, name='reset_user_password'),
    path('employee/admin/bulk-action/', views_admin.bulk_action, name='bulk_action'),
    
    # Project Board URLs
    path('employee/boards/', views_boards.project_boards, name='project_boards'),
    path('employee/boards/create/', views_boards.create_board, name='create_board'),
    path('employee/boards/<uuid:board_id>/', views_boards.board_detail, name='board_detail'),
    path('employee/boards/<uuid:board_id>/delete/', views_boards.delete_board, name='delete_board'),
    path('api/boards/<uuid:board_id>/lists/create/', views_boards.create_list, name='create_list'),
    path('api/boards/<uuid:board_id>/members/', views_boards.get_board_members, name='get_board_members'),
    path('api/boards/<uuid:board_id>/members/add/', views_boards.add_board_member, name='add_board_member'),
    path('api/boards/<uuid:board_id>/members/remove/', views_boards.remove_board_member, name='remove_board_member'),
    path('api/employees/search/', views_boards.search_employees, name='search_employees'),
    path('api/lists/<uuid:list_id>/cards/create/', views_boards.create_card, name='create_card'),
    path('api/cards/<uuid:card_id>/', views_boards.card_detail, name='card_detail'),
    path('api/cards/<uuid:card_id>/update/', views_boards.update_card, name='update_card'),
    path('api/cards/<uuid:card_id>/comments/', views_boards.add_card_comment, name='add_card_comment'),
    path('api/cards/move/', views_boards.move_card, name='move_card'),
]
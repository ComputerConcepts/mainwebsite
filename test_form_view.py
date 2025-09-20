from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_form_builder(request):
    """Standalone test page for form builder"""
    with open('test_form_builder_standalone.html', 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/html')
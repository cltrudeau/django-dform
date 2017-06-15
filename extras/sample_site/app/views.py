from django.shortcuts import render
from dform.models import SurveyVersion

from awl.utils import render_page

def embed(request):
    sv = SurveyVersion.objects.first()
    return render_page(request, 'embed.html', {'survey_version':sv})

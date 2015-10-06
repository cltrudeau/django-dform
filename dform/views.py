import json, logging
from collections import OrderedDict
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404

from awl.decorators import post_required
from awl.utils import render_page

from .fields import FIELDS_DICT
from .models import (EditNotAllowedException, Survey, SurveyVersion, Question,
    QuestionOrder)

logger = logging.getLogger(__name__)

# ============================================================================
# AJAX Methods 
# ============================================================================

@post_required(['delta'])
def survey_delta(request, survey_version_id):
    delta = json.loads(request.POST['delta'], object_pairs_hook=OrderedDict)
    if survey_version_id == '0':
        # new survey
        survey = Survey.objects.create(name=delta['name'])
        version = survey.latest_version
    else:
        version = get_object_or_404(SurveyVersion, id=survey_version_id)
        survey = version.survey

    try:
        survey.replace_from_dict(delta, version)
    except EditNotAllowedException:
        raise Http404('Survey %s is not editable' % version.survey)
    except Question.DoesNotExist as dne:
        raise Http404('Bad question id: %s' % dne)

    # issue a 200 response
    return HttpResponse()

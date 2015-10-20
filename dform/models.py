# dform.models.py
import logging, collections

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.encoding import python_2_unicode_compatible

from jsonfield import JSONField
from awl.models import TimeTrackModel
from awl.rankedmodel.models import RankedModel

from .fields import FIELD_CHOICES, FIELDS_DICT

logger = logging.getLogger(__name__)

# ============================================================================
# Survey Management
# ============================================================================

class EditNotAllowedException(Exception):
    pass


@python_2_unicode_compatible
class Survey(TimeTrackModel):
    name = models.CharField(max_length=50)
    success_redirect = models.TextField()

    def __str__(self):
        return 'Survey(id=%s %s)' % (self.id, self.name)

    @transaction.atomic
    def new_version(self):
        """Creates a new version of the ``Survey``, associating all the
        current verion's questions with the new version.  Note, this will have
        the side effect of changing the latest version of this ``Survey``.

        :returns:
            newly created :class:`SurveyVersion`
        """
        old_version = self.latest_version
        new_version = SurveyVersion.objects.create(survey=self,
            version_num=self.latest_version.version_num + 1)

        orders = QuestionOrder.objects.filter(
            survey_version=old_version).order_by('rank')
        for order in orders:
            QuestionOrder.objects.create(survey_version=new_version,
                question=order.question, rank=order.rank)
            order.question.survey_versions.add(new_version)

        return new_version

    @property
    def latest_version(self):
        return SurveyVersion.objects.filter(survey=self).order_by(
            '-version_num')[0]

    # ---------
    # Methods on Latest Version

    def add_question(self, field, text, rank=0, required=False, 
            field_parms={}):
        """Convenience method for :func:`SurveyVersion.add_question` using
        the latest version.

        :param field: 
            a :class:`Field` instance describing the kind of question being
            created
        :param text:
            text to display when asking the question
        :param rank:
            the order number of this question, defaults to 0 which means
            insert last
        :param required:
            whether the question is required for form submission
        :param field_parms:
            a field specific dictionary specifying parameters for the use of
            the field.  
        :returns:
            newly created :class:`Question` object
        :raises EditNotAllowedException:
            editing is not allowed for surveys that already have answers
        """
        return self.latest_version.add_question(field, text, rank, required,
            field_parms)
        
    def remove_question(self, question):
        """Convenience method for :func:`SurveyVersion.remove_question` using
        the latest version.

        :param question:
            :class:`Question` to be removed
        :raises EditNotAllowedException:
            editing is not allowed for surveys that already have answers
        """
        return self.latest_version.remove_question(question)


    def questions(self):
        """Convenience method for :func:`SurveyVersion.questions` on latest
        version of survey.
        
        :returns:
            list of :class:`Question` objects
        """
        return self.latest_version.questions()

    def answer_question(self, question, answer_group, value):
        """Convenience method for :func:`SurveyVersion.answer_question` on
        latest version of survey.

        :param question:
            :class:`Question` that is being answered.  It must be a valid
            question for this version of the survey
        :param answer_group:
            A number that groups together the answers for a survey.  An
            example would be to use the user's id so that all of their answers
            are grouped together.  This would mean each user could only answer
            each survey once.
        :param value:
            Value to record as an answer.  The value is validated against the
            field associated with the :class:`Question`.

        :raises ValidationError:
            If the value given does not pass the question's field's validation
        :raises AttributeError:
            If the question is not attached to this version of the
            ``Survey``
        """
        return self.latest_version.answer_question(question, answer_group,
            value)

    def to_dict(self):
        """Convenience method for :func:`SurveyVersion.to_dict` on the latest
        version of the survey.
        """
        return self.latest_version.to_dict()

    def replace_from_dict(self, data):
        """Convenience method for :func:`SurveyVersion.replace_from_dict` on
        the latest version of the survey.

        :param data:
            Dictionary to overwrite the contents of the ``Survey` and
            associated :class:`Question` objects with.
        :raises EditNotAllowedException:
            If the version being replaced is active
        :raises Question.DoesNotExist:
            If a question id is referenced that does not exist or is not
            associated with this survey.
        """
        return self.latest_version.replace_from_dict(data)


@receiver(post_save, sender=Survey)
def survey_post_save(sender, **kwargs):
    if kwargs['created']:
        # newly created object, create a version to go with it
        SurveyVersion.objects.create(survey=kwargs['instance'])


@python_2_unicode_compatible
class SurveyVersion(TimeTrackModel):
    survey = models.ForeignKey(Survey)
    version_num = models.PositiveSmallIntegerField(default=1)
    success_redirect = models.TextField(blank=True)

    def __str__(self):
        return 'SurveyVersion(id=%s survey=%s, num=%s)' % (self.id, 
            self.survey.name, self.version_num)

    class Meta:
        verbose_name = 'Survey Version'

    def validate_editable(self):
        if Answer.objects.filter(
                answer_group__survey_version=self).count() != 0:
            raise EditNotAllowedException()

    def is_editable(self):
        count = Answer.objects.filter(answer_group__survey_version=self).count()
        return count == 0

    def on_success(self):
        """Called when this survey version has been successfully submitted.
        Uses the ``success_redirect`` field, if it is empty then uses the
        associated :class:`Survey` object's ``success_redirect`` field.  The
        fields is processed as a django template with this survey version as
        context and the result is returned.
        """
        redirect = self.survey.success_redirect
        if self.success_redirect:
            redirect = self.success_redirect

        template = Template(redirect)
        context = Context({'survey_version':self})
        return template.render(context)

    def add_question(self, field, text, rank=0, required=False, field_parms={}):
        """Creates a new :class:`Question` for this ``SurveyVersion``.

        :param field: 
            a :class:`Field` instance describing the kind of question being
            created
        :param text:
            text to display when asking the question
        :param rank:
            the order number of this question, defaults to 0 which means
            insert last
        :param required:
            whether the question is required for form submission
        :param field_parms:
            a field specific dictionary specifying parameters for the use of
            the field.  
        :returns:
            newly created :class:`Question` object
        :raises EditNotAllowedException:
            editing is not allowed for surveys that already have answers
        """
        self.validate_editable()

        field.check_field_parms(field_parms)
        question = Question.objects.create(survey=self.survey, text=text,
            field_key=field.field_key, required=required,
            field_parms=field_parms)
        question.survey_versions.add(self)

        kwargs = {
            'survey_version':self,
            'question':question,
        }
        if rank != 0:
            kwargs['rank'] = rank

        QuestionOrder.objects.create(**kwargs)
        return question

    def remove_question(self, question):
        """Removes the given question from this ``SurveyVersion``. 

        :param question:
            :class:`Question` to be removed
        :raises EditNotAllowedException:
            editing is not allowed for surveys that already have answers
        """
        self.validate_editable()
        question.survey_versions.remove(self)
        QuestionOrder.objects.get(question=question, 
            survey_version=self).delete()

    def questions(self):
        """Returns an iterable of the questions for this survey version in
        order.

        :returns:
            list of :class:`Question` objects
        """
        orders = QuestionOrder.objects.filter(survey_version=self
            ).order_by('rank')
        return [order.question for order in orders]

    def answer_question(self, question, answer_group, value):
        """Record an answer to the given question in this version of the
        survey.

        :param question:
            :class:`Question` that is being answered.  It must be a valid
            question for this version of the survey
        :param answer_group:
            A number that groups together the answers for a survey.  An
            example would be to use the user's id so that all of their answers
            are grouped together.  This would mean each user could only answer
            each survey once.
        :param value:
            Value to record as an answer.  The value is validated against the
            field associated with the :class:`Question`.

        :raises ValidationError:
            If the value given does not pass the question's field's validation
        :raises AttributeError:
            If the question is not attached to this version of the
            ``Survey``
        """
        try:
            # make sure this question is registered against this survey
            # version
            question.survey_versions.get(id=self.id)
        except SurveyVersion.DoesNotExist:
            raise AttributeError()

        return Answer.factory(question, answer_group, value)

    def to_dict(self):
        """Returns a dictionary representation of this survey version.

        Format:

        .. code-block::python

            {
                'name':survey_name,
                'questions':[
                    {
                        'id':question_id,
                        'field_key':question_field_key,
                        'text':question_text,
                        'required':is_question_required,
                        'field_params:OrderedDict(*field_parm_tuples),
                    }
                ]
            }

        .. note::

            The order of the question dictionaries will be the order of the
            questions in the survey.

        .. note::

            Be careful to use a ``OrderedDict`` with the field parameters, as
            the order of parameters is used for the order of display in
            multiple choice style questions.
        """
        questions = []
        for question in self.questions():
            questions.append({
                'id':question.id,
                'field_key':question.field_key,
                'text':question.text,
                'required':question.required,
                'field_parms':question.field_parms,
            })

        data = {
            'name':self.survey.name,
            'questions':questions,
        }

        return data

    def replace_from_dict(self, data):
        """Takes the given dictionary and modifies this survey version and its
        associated questions.  Uses the same format as 
        :func:`SurveyVersion.to_dict` with one additional (optional) key
        "remove" which contains a list of :class:`Question` ids to be removed
        from the ``Survey``.

        :param data:
            Dictionary to overwrite the contents of the ``Survey` and
            associated :class:`Question` objects with.
        :raises EditNotAllowedException:
            If the version being replaced is active
        :raises Question.DoesNotExist:
            If a question id is referenced that does not exist or is not
            associated with this survey.
        """
        self.validate_editable()

        if 'name' in data:
            self.survey.name = data['name']
            self.survey.save()

        if 'questions' in data:
            for q_data in data['questions']:
                if q_data['id'] == 0:
                    # new question
                    kwargs = {
                        'field':FIELDS_DICT[q_data['field_key']],
                        'text':q_data['text'],
                        'required':q_data['required'],
                        'field_parms':q_data['field_parms'],
                    }

                    # add the question and set the data's question id so that we
                    # can do re-ordering down below
                    question = self.add_question(**kwargs)
                    q_data['id'] = question.id
                else:
                    question = Question.objects.get(id=q_data['id'],
                        survey_versions__id=self.id)
                   
                    question.text = q_data['text']
                    question.required = q_data['required']
                    question.field_parms = q_data['field_parms']
                    question.save()

        # fix the ranking -- creating new questions will mess with the order
        if 'questions' in data:
            for index, q_data in enumerate(data['questions']):
                question = Question.objects.get(id=q_data['id'],
                    survey_versions__id=self.id)

                q_order = QuestionOrder.objects.get(question=question,
                    survey_version=self)
                q_order.rank = index + 1
                q_order.save(rerank=False)

        if 'remove' in data:
            for id in data['remove']:
                question = Question.objects.get(id=id,
                    survey_versions__id=self.id)
                self.remove_question(question)

# ============================================================================
# Question & Answers
# ============================================================================

@python_2_unicode_compatible
class Question(TimeTrackModel):
    survey = models.ForeignKey(Survey)
    survey_versions = models.ManyToManyField(SurveyVersion)

    text = models.TextField(blank=True)
    field_key = models.CharField(max_length=2, choices=FIELD_CHOICES)
    field_parms = JSONField(default={}, blank=True,
        load_kwargs={'object_pairs_hook':collections.OrderedDict})
    required = models.BooleanField(default=False)

    def __str__(self):
        return 'Question(id=%s %s:%s)' % (self.id, self.field_key,
            self.short_text)

    @property
    def field(self):
        return FIELDS_DICT[self.field_key]

    def field_choices(self):
        choices = []
        for k, v in self.field_parms.items():
            choices.append((k, v))

        return choices

    @property
    def short_text(self):
        """Returns a short version of the question text.  Any thing longer
        than 15 characters is truncated with an elipses."""
        text = self.text
        if len(text) >= 15:
            text = text[:12] + '...'

        return text

    def render(self):
        data = {
            'question':self,
        }
        return render_to_string(self.field.template, data)


@python_2_unicode_compatible
class QuestionOrder(TimeTrackModel, RankedModel):
    survey_version = models.ForeignKey(SurveyVersion)
    question = models.ForeignKey(Question)

    class Meta:
        verbose_name = 'Question Order'
        verbose_name_plural = 'Question Order'
        ordering = ['survey_version__id', 'rank']

    def __str__(self):
        return 'QuestionOrder(id=%s, rank=%s sv.id=%s q.id=%s)' % (self.id,
            self.rank, self.survey_version.id, self.question.id)

    def grouped_filter(self):
        return QuestionOrder.objects.filter(
            survey_version=self.survey_version).order_by('rank')


@python_2_unicode_compatible
class AnswerGroup(TimeTrackModel):
    survey_version = models.ForeignKey(SurveyVersion)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(default=0)
    group_data = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Answer Group'

    def __str__(self):
        return 'AnswerGroup(id=%s data=%s)' % (self.id, self.group_data)


@python_2_unicode_compatible
class Answer(TimeTrackModel):
    question = models.ForeignKey(Question)
    answer_group = models.ForeignKey(AnswerGroup)

    answer_text = models.TextField(blank=True)
    answer_key = models.TextField(blank=True)
    answer_float = models.FloatField(null=True, blank=True)

    def __str__(self):
        return 'Answer(id=%s ag.id=%s q.id=%s value=%s)' % (self.id, 
            self.answer_group.id, self.question.id, self.display_value)

    @classmethod
    def factory(cls, question, answer_group, value):
        question.field.check_value(question.field_parms, value)
        kwargs = {
            'answer_group':answer_group,
            'question':question,
        }
        kwargs[question.field.storage_key] = value
        
        try:
            answer = Answer.objects.get(question=question,
                answer_group=answer_group)
            setattr(answer, question.field.storage_key, value)
            answer.save()
        except Answer.DoesNotExist:
            return Answer.objects.create(**kwargs)

    @property
    def value(self):
        """Returns the value stored in this ``Answer``.  Note that the type of
        the data returned may be a string or float depending on what is
        stored.
        """
        return getattr(self, self.question.field.storage_key)

    @property
    def display_value(self):
        """Returns a string version of the value limited to 15 characters.
        """
        value = str(self.value)
        if len(value) >= 15:
            value = value[:12] + '...'

        return value

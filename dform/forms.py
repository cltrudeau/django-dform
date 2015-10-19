# dform.forms.py
from django import forms
from django.template.loader import render_to_string

from .fields import FIELDS_DICT, ChoiceField, Rating

# ============================================================================

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.survey_version = kwargs.pop('survey_version')
        self.answer_group = kwargs.pop('answer_group', None)

        if 'initial' in kwargs:
            raise AttributeError(
                '"initial" keyword is not allowed with SurveyForm')

        super(SurveyForm, self).__init__(*args, **kwargs)

        if len(args) > 0:
            post = args[0]
        else:
            post = {}

        self.populate_fields(post)

    def populate_fields(self, values):
        for question in self.survey_version.questions():
            name = 'q_%s' % question.id

            kwargs = {
                'label':question.text,
                'required':question.required,
            }

            if name in values:
                kwargs['initial'] = values[name]

            if question.field.django_widget:
                kwargs['widget'] = question.field.django_widget

            if question.field == Rating:
                kwargs['choices'] = (
                    (5, '5 Star'),
                    (4, '4 Star'),
                    (3, '3 Star'),
                    (2, '2 Star'),
                    (1, '1 Star'),
                )
            elif issubclass(question.field, ChoiceField):
                kwargs['choices'] = question.field_choices()

            field = question.field.django_field(**kwargs)
            field.question = question
            if question.field.form_control:
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'

            self.fields[name] = field

    def render_form(self):
        return render_to_string('dform/fields.html', {'form':self})
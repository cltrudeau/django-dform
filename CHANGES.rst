0.9.2
=====

* bug fixes for the bug fixes, some of the last commit didn't get included 

0.9.1
=====

* fixed bug where the Survey Show Title check box changes weren't saved

0.9.0
=====

* changed supported versions: Python 3.6, 3.5, 2.7; Django 1.9, 1.10
* added documentation on Apache X-Frame-Options header
* removed reCAPTCHA capabilities: was very broken, will likely integrate with
    another library in the future to provide this feature
* add "show_title" option so the survey name can be hidden from the survey
    form when it is displayed
* changed display string for Question to include a reference to the Survey,
    makes it easier to pick the right one in the django admin

0.8.1
=====

* fixed: Email field was missing from survey editor

0.8.0
=====

* implement submit and edit call-back hooks
* add Google reCAPTCHA capabilities
* added views for getting latest survey
* added Email field
* added IP Address tracking on the survey submit

0.7.0
=====

* changed "Add Survey" button in django admin to use Survey Editor

0.6.1
=====

* made python 3.5 and django 1.10 compatible
* fixed missing migrations

0.5
===

* changed over survey links to now use a dedicated token, not secure but helps
    prevent cross survey guessing based on the URL
* added admin pages for showing sample HTML to paste into your web pages to
    link to or embed a survey
* added use of pym.js to handle responsive pages when doing a embedded IFRAME
    inclusion of a form
* removed a bunch of unused imports

0.3
===

* finished tests, now supports python 2.7

0.2
===

* finished main feature set
* added documentation

0.1
===

* initial commit to pypi

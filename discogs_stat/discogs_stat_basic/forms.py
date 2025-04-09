from django.forms import Form, CharField


class NicknameRequestForm(Form):
    discogs_nickname = CharField(max_length=50)
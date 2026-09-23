from accounts.models import User


def set_created_by_choices(form):
    users = User.objects.order_by('email', 'mobile')
    choices = [('', '---------')]
    choices.extend((str(user.pk), str(user)) for user in users)

    current_created_by = form.initial.get('created_by')
    choice_values = {value for value, _ in choices}
    if current_created_by and current_created_by not in choice_values:
        choices.append((current_created_by, current_created_by))

    form.fields['created_by'].choices = choices

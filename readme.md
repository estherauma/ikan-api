## Tuna Application


## Structure and set up

This app is a django project and is structured to use to multiple settings file defined in:

```
settings/
   base.py  # contains the base default app settings
   ci.py   # contains the ci tool settings
   dev.py  # contains the development app settings
   prod.py # contains the production app settings
   staging.py # contains the staging app settings
```
## Running tests
1. `coverage run manage.py test` to run tests
1. `coverage report` to generate test report

## WebHooks
The app has some webooks that run with it. e.g. wheh content is updated on prismic, the app is notified via a webhook.
When developing, refer to this [article](https://geekflare.com/expose-django-app-with-ngrok/) to see how the app can get updated content while developing

## Setting up email
To setup email sending in the application
1. add the values for the following env variables
```
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
APPLICATION_FROM_EMAIL=
```

2. import the `TunaEmailHelper` class and  `EmailTemplate` as well if sending templated email.
3. example
i) without template
```
TunaEmailHelper.tuna_send_email(
   to_emails=[config('APPLICATION_FROM_EMAIL')],
   subject='Call for Applications: Software Developer at Tuna Inc',
   body='Application for the above position'
)
```

ii) with template (must pass the template parameter which can be accessed from `EmailTemplate`)
```
TunaEmailHelper.tuna_send_email(
   template=EmailTemplate.APPLICATION.value,
   to_emails=[config('APPLICATION_FROM_EMAIL')],
   subject='Call for Applications: Software Developer at Tuna Inc',
   body='Application for the above position'
)
```

## Test users and roles
The app mobile depends on the roles defined in `accounts.management.commands` to work correctly.
The management command above creates the default roles  and some users to begin with.
If you are setting up a new installation, ensure that you set up those roles.
To run the command, just run `python manage.py seedusersandroles`

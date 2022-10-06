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

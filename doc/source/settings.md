# Settings

This will be the reference of available settings.

## Declaring email types

As there is no auto-discovery of email types, you need to declare them yourself
using the `WAILER_EMAIL_TYPES` setting.

By example:

```python
WAILER_EMAIL_TYPES = {
    "static": "my_app.emails.Static",
    "static-no-text": "my_app.emails.StaticNoText",
    "static-no-html": "my_app.emails.StaticNoHtml",
    "hello": "my_app.emails.Hello",
    "hello-user": "my_app.emails.HelloUser",
    "styled-html": "my_app.emails.StyledHtml",
}
```

## Setting the base URL

When generating absolute links from inside the email, several settings can be
used:

- `WAILER_BASE_URL` &mdash; To manually set the base URL of your site
- `WAILER_SITE_ID` &mdash; To select a site from the sites framework
- `SITE_ID` &mdash; Not wailer-specific, that's a setting from the sites 
  framework that will determine which is the default site to use

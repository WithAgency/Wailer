# Backends

Wailer comes with its own backends for email and SMS sending (based of course on
external services).

This ensures:

-   No extra library is depended upon
-   All requests have proper timeouts (aka not made with requests)
-   Everything is maintained at each release

## Emails

### Mailjet

In order to use Mailjet, you need to set the following Django settings:

-   `EMAIL_BACKEND` &mdash; Must be set to
    `"wailer.backends.MailjetEmailBackend"`
-   `MAILJET_API_KEY_PUBLIC` &mdash; Contains the public API key
-   `MAILJET_API_KEY_PRIVATE` &mdash; Contains the private API key

## SMS

### Mailjet

Uses the Mailjet SMS service. Once it's configured and paid for, you can set the
following settings:

-   `SMS_BACKEND` &mdash; Must be set to ` "wailer.backends.MailjetSmsBackend"`
-   `MAILJET_API_TOKEN` &mdash; Is the API Token that you get from the Mailjet
    console

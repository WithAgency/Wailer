# Backends

Wailer comes with its own backends for email and SMS sending (based of course on
external services).

This ensures:

- No extra library is depended upon
- All requests have proper timeouts (aka not made with requests)
- Everything is maintained at each release

## Emails

### Mailjet

In order to use Mailjet, you need to set the following Django settings:

- `EMAIL_BACKEND` &mdash; Must be set to `"wailer.backends.MailjetEmailBackend"`
- `MAILJET_API_KEY_PUBLIC` &mdash; Contains the public API key
- `MAILJET_API_KEY_PRIVATE` &mdash; Contains the private API key

### Mandrill

An Mandrill backend is also available.

- `EMAIL_BACKEND` &mdash; Must be set to
  `"wailer.backends.MandrillEmailBackend"`
- `MANDRILL_API_KEY` &mdash; Contains the API key

Django only lets a backend report how many messages went out, so a message
Mandrill refuses (unsigned sender domain, invalid recipient, bad API key)
would otherwise disappear behind a count of zero. The backend logs every
refusal as an error on the `wailer.backends.mandrill` logger, naming the
sender, the recipient and the reason Mandrill gives, so that it shows up in
your logs and in your error tracker if one reads them.

## SMS

### Mailjet

Uses the Mailjet SMS service. Once it's configured and paid for, you can set the
following settings:

- `SMS_BACKEND` &mdash; Must be set to `"wailer.backends.MailjetSmsBackend"`
- `MAILJET_API_TOKEN` &mdash; Is the API Token that you get from the Mailjet
  console

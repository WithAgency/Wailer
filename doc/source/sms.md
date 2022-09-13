# Sending SMSes

Django doesn't have an abstraction for sending SMSes, however there is the
[Django SMS](https://pypi.org/project/django-sms/) package that basically
duplicates the email API for SMS. Wailer is based upon this package and even
provides its own backends.

Everything in the SMS API is very similar to the email API and we'll write this
documentation assuming that you already know how emails work.

## Building the class

Our example will be a simple SMS of courtesy, to be able to say hello.

### SmsType

The first thing to do is to extend {py:class}`~.wailer.interfaces.SmsType`.

```python
from wailer.interfaces import SmsType

class HelloUser(SmsType):
    pass
```

### Sender

Next you need to give a sender. That entirely depends on your backend. If you're
using Mailjet, you can just put there the name of your application. Other
providers will ask you to register different phone numbers for different
countries.

Overall the logic is entirely up to you. You're free to implement any logic and
it will be passed down to the backend, without any validation (which makes it a
double-edged sword).

In our case, we'll assume Mailjet and do something simple:

```python
    def get_from(self) -> str:
        return "Wailer"
```

### User and context

We'll expect to receive in the data the `user_id`, which we can then exploit in
particular when making the context.

```python
    @cached_property
    def user(self):
        return User.objects.get(pk=self.data["user_id"])

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.user.first_name} {self.user.last_name}",
            locale=self.user.locale,
        )
```

### Recipient

Now we're sending this SMS to the user's phone number. You obviously need it
somewhere. In our case, that's in the user model.

```python
    def get_to(self) -> str:
        return self.user.phone_number
```

It's expected to be something that libphonenumber can parse.

### Content

Just like for emails, you need to decide which locale you will use. The locale
will be activated during content render.

```python
    def get_locale(self) -> str:
        return self.context["locale"]

    def get_content(self) -> str:
        return _(f"Hello %(name)s") % dict(name=self.context["name"])
```

Let's also note that if you wanted to make a link to the website itself, it's
easy to get an absolute URL to insert into your content:

```python
    def get_content(self) -> str:
        return _("Hello %(name)s, come home to: %(url)s") % dict(
            name=self.context["name"],
            url=self.make_absolute("/"),
        )
```

## Registering the type

You need to register your email type in `settings.py`, much like you would for
emails:

```python
WAILER_SMS_TYPES = {
    "hello-user": "my_app.sms.HelloUser",
}
```

## Sending the SMS

In order to send the SMS from your code, you can simply:

```python
Sms.send("hello-user", dict(user_id=user.id), user)
```

## Conclusion

Sending SMSes is a simpler version of email sending with a very similar
interface and much less concern.

Let's however note that depending on the backend you choose, you might be up to
a different range of difficulties, given how tight and variable the regulation
can be in various countries.

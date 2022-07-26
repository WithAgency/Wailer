# Sending Emails

Wailer sends emails using Django's emailing system but with a few layers on top
to make sure that it's easy and safe to do. Notably it will help you generate
your emails through the template engine while making sure of important details.

Each email that you send will have:

- A type &mdash; Determines which template to use and the email's overall
  behavior
- Some associated data &mdash; Seed for the email's content, that will serve to
  generate the template

## Saying hello

Suppose we want to send an email to say hello to someone whose name we know.

The message we want to send is something intellectual like:

```
Hello John Doe!

Cheers mate
```

You need to create your own email types. Their job is to transform the input
data into what is going to be the sent email.

To do so, all you need to do is implement the 
{py:class}`~.wailer.interfaces.EmailType`, which has a bunch of abstract 
methods.

### Stub

Let's start with a stub of all the abstract methods you need to implement:

```python
class Hello(EmailType):
    def get_to(self) -> str:
        raise NotImplementedError

    def get_locale(self) -> str:
        raise NotImplementedError

    def get_context(self) -> Mapping[str, JsonType]:
        raise NotImplementedError

    def get_subject(self) -> str:
        raise NotImplementedError

    def get_template_html_path(self) -> str:
        raise NotImplementedError

    def get_template_text_path(self) -> str:
        raise NotImplementedError
```

You can put this in any file you want, but conventionally you can create an
`emails.py` file at the root of your app.

### Target

Before implementing this, let's have a look at how we're going to send this
email.

```python
from wailer.models import Email

Email.send(
    "hello",
    dict(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.org",
        locale="fr",
    ),
)
```

The first argument (`"hello"`) is the ID of the type. We'll see about it later.
The second argument is a dictionary containing the `data` of that email. This
is the source material that you're transforming into an email. The values
should be JSON-serializable. From type implementation, you can access the data
using `self.data`.

### Building up

Let's dive into each method.

```python
    def get_to(self) -> str:
        return self.data["email"]
```

Here we return the email address of the recipient. In that case it comes
straight from the data.

```python
    def get_locale(self) -> str:
        return self.data["locale"]
```

When sending the email, you need to make sure that it's sent using the locale
of the recipient.

```{note}
If you send the email as part of the code of a view, Django will be making sure
that the locale currently in use is the one that the user asked for. However
when you send an email from a background task, you're not doing that as part of
a HTTP response. Thus, Django doesn't know the current locale to apply and will
use your default locale instead. It's your responsibility to make sure to
record which is the user's locale for this email.
```

```python
    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.data['first_name']} {self.data['last_name']}",
            email=self.data["email"],
        )
```

Here we generate the context that we're going to provide to the HTML and text
templates. You're typically going to be doing this by copying/transforming
things from your data.

You're going to ask, but why the fuck are we not reading the data directly
instead of computing the context? Well, by example in the data you can store
some object IDs while in the context you can save properties related from these
objects.

```{note}
When you send an email, the content will not change in the future. This means
that you should be able to re-render the same email again if the user asks you
to (by example the "click here to see this email in a browser" link).

As a result, the {py:meth}`~.wailer.interfaces.EmailType.get_context` method
will be called only once and then its output will be stored into database.
Meaning that if the output of
{py:meth}`~.wailer.interfaces.EmailType.get_context` depends on DB data that
could change, it will be frozen to the state at the moment of the email.
```

```python
    def get_subject(self) -> str:
        return _(f"Hello %(name)s") % dict(name=self.context["name"])
```

This one will look fairly obvious, we're just generating the text of the
subject. The locale will be guaranteed to be set.

```python
    def get_template_html_path(self) -> str:
        return "my_app/wailer/hello.html"

    def get_template_text_path(self) -> str:
        return "my_app/wailer/hello.txt"
```

Here we simply return the location of the template files for the HTML and text.

### Final result

Here is what it should look at the end:

```python
class Hello(EmailType):
    def get_to(self) -> str:
        return self.data["email"]

    def get_locale(self) -> str:
        return self.data["locale"]

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.data['first_name']} {self.data['last_name']}",
            email=self.data["email"],
        )

    def get_subject(self) -> str:
        return _(f"Hello %(name)s") % dict(name=self.context["name"])

    def get_template_html_path(self) -> str:
        return "my_app/wailer/hello.html"

    def get_template_text_path(self) -> str:
        return "my_app/wailer/hello.txt"
```

### Registering

Next you need to tell the system that this email type is available. You need
to add this to your `settings.py`:

```python
WAILER_EMAIL_TYPES = {
    "hello": "my_app.emails.Hello",
}
```

And we're all done! You can go run the code from the "Target" section above and
send emails.

## Data availability

You must have noticed that not everything is available all the time. Let's have
a recap.

|                            | `self.data` | `self.context` | locale |
|----------------------------|-------------|----------------|--------|
| `get_to()`                 | Yes         | No             | No     |
| `get_context()`            | Yes         | No             | No     |
| `get_locale()`             | Discouraged | Yes            | No     |
| `get_subject()`            | Discouraged | Yes            | Yes    |
| `get_template_html_path()` | Discouraged | Yes            | Yes    |
| `get_template_text_path()` | Discouraged | Yes            | Yes    |
| `get_attachments()`        | Discouraged | Yes            | Yes    |

## With live data

The previous example is a bit twisted in the sense that usually emails will be
related to actual users and live data from the DB. Here we're going to
demonstrate how to do this.

### Storing locale

The first thing is to make sure that we know the user's locale at any time.
A very simple implementation would be to store the user's favorite locale in
the user model, like this:

```python
class User(AbstractUser):
    locale = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
    )
```

Of course that's just an example, the way to store the user's locale is
completely up to you and depends a lot on your business logic.

### Modifying the code

Instead of giving `first_name`, `last_name` and so forth as data, we'll just
provide the user ID.

That is our new target code for email sending:

```python
email = Email.send("hello", dict(user_id=user.id), user)
```

Let's note that as opposed to before, we're giving a third `user` parameter.
The goal is to optionally be able to link an email to a user so that when you
delete the user all the related emails (and their PII) can be deleted at the
same time.

Then we add to our email type a way to easily get the user.

```python
    @cached_property
    def user(self):
        return User.objects.get(pk=self.data["user_id"])
```

Next, let's modify the subsequent functions to get the information we need 
from the user object.

```python
    def get_to(self) -> str:
        return self.user.email

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.user.first_name} {self.user.last_name}",
            email=self.user.email,
            locale=self.user.locale,
        )

    def get_locale(self) -> str:
        return self.context["locale"]
```

You'll note that the locale comes from the `context`. That's because if the
user changes their locale, they still need to see that old email in the old
locale.

The rest of the code doesn't need to be changed, you're good to go!

### Overview

Just for posterity, here is an overview of the finished class

```python
class Hello(EmailType):
    @cached_property
    def user(self):
        return User.objects.get(pk=self.data["user_id"])
    
    def get_to(self) -> str:
        return self.user.email

    def get_locale(self) -> str:
        return self.context["locale"]

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.user.first_name} {self.user.last_name}",
            locale=self.user.locale,
        )

    def get_subject(self) -> str:
        return _(f"Hello %(name)s") % dict(name=self.context["name"])

    def get_template_html_path(self) -> str:
        return "my_app/wailer/hello.html"

    def get_template_text_path(self) -> str:
        return "my_app/wailer/hello.txt"
```

## Skipping text or HTML

If you don't want to send either the text or the HTML part of your email, it's
easy to skip it by throwing a `NotImplementedError` while returning the
template path. By example if you're lazy to write a HTML version of your email
you can just do:

```python
    def get_template_html_path(self) -> str:
        raise NotImplementedError
```

## Advanced topics

HTML emails are the most notoriously annoying kind of HTML to write. It did not
evolve since its invention by Leonardo da Vinci in 1495 and email clients have
quite an interesting approach of making the most dumb choices available to
them.

One of the goals of Wailer is definitely to ease that pain. Let's review what
can help.

### Automatic style inline

Most email clients will ignore any `<style>` or `<link>` tag, making it
mandatory to inline CSS into every single element. So what Wailer provides here
is the ability to write your CSS file on the side and then inline it for you.

Let's suppose that you put in your static files the 
`my_app/wailer/styled-html.css` (relative to your app's 
[static folder](https://docs.djangoproject.com/en/4.0/howto/static-files/)) 
file with the following content:

```css
h1 {
    color: red;
}
```

And then your template, in `my_app/wailer/styled-html.html`:

```html
{% load wailer %}
<!DOCTYPE html>
<html>
<head>
    {% email_style "my_app/wailer/styled-html.css" %}
</head>
<body>
    <h1>Hello</h1>
</body>
</html>
```

A few important things to notice:

- The wailer template tags are loaded through `{% load wailer %}`
- The `{% email_style %}` template tag is used in situ of where you would load
  your style in normal conditions (in the `<head>`)

Thanks to this, the CSS will get inlined in the CSS. The output will contain
something like:

```html
<!-- ... -->
    <h1 style="color:red">Hello</h1>
<!-- ... -->
```

```{note}
This won't work with media queries, as they can't be inlined. Life sucks I
know.
```

```{note}
Under the hood, all the work is done by 
[Premailer](https://pypi.org/project/premailer/) using fairly default options
as much as possible.
```

(absolute_url)=
### Absolute URLs for images and links in HTML

Since you're in an email, you need to use absolute URLs. By example, if you
have a `<img src="/img/foo.jpg">` then it simply  won't work because the emails
don't have an URL of their own so the email client cannot resolve this image's
URL.

To that end, Wailer will automatically fix your links and emails in order to
reflect their absolute URL. By example our image tag from above will 
automatically be transformed into `<img src="https://my-app.com/img/foo.jpg>` 
(if your base URL is `https://my-app.com`, cf right after). You don't have 
anything to do, just render your template as usual and let the magic happen.

However there is one detail that you might want to have a look into. There is
no bulletproof way in Django to determine the absolute domain name of a 
website. To that end, Wailer will use several strategies.

1. If there is a `WAILER_BASE_URL` setting set, then this value will be used as 
   a base URL for all emails
2. Otherwise we'll try to use the 
   ["sites"](https://docs.djangoproject.com/en/4.0/ref/contrib/sites/) 
   framework, if available
   1. If `WAILER_SITE_ID` is defined in the settings, we'll use that
   2. Otherwise we'll get the default site. We do not have access to the 
      `request` at the time of sending emails so if you're dealing with several 
      websites you need to implement this on your own
3. Otherwise, we'll just fail because there is really no way of guessing

This tries to be a sensible default behavior, which will work without any
configuration if you're using the sites framework with one site, however this
will most definitely not be enough for all use cases. This is why you can 
easily override this behavior in your {py:class}`~.wailer.interfaces.EmailType`
implementation by overloading 
{py:meth}`~.wailer.interfaces.BaseMessageType.get_base_url`.

### Absolute URLs programmatically

If you need absolute URLs but you're not writing them in HTML (and thus the
automatic insertion of the base URL won't work like above), then some template
tags are here to help you.

#### Make absolute

If you have an URL and you want to make it absolute, you can do it like that:

```html
{% load wailer %}

{% make_absolute "/foo/bar" %}
<!-- Will output https://my-app.com/foo/bar -->
```

#### Absolute URL

Wailer also provides an absolute version of Django's 
[`{% url %}`](https://docs.djangoproject.com/en/4.0/ref/templates/builtins/#url) 
tag. It works exactly the same way except it will output URLs that are 
absolute.

```html
{% load wailer %}

{% absolute_url "my_view" %}
<!-- Will output https://my-app.com/my-view -->
```

### Permalink to email

Wailer lets you create permalinks to your emails, for two main reasons:

- So you can put in the header something like "If this email isn't displayed
  properly, then click on this link"
- But mostly, so you can debug your HTML code without sending a damned email
  each time you change a line

This is accessible as the
{py:attr}`~.wailer.models.Email.link_html` and
{py:attr}`~.wailer.models.Email.link_text` attributes of your email.

Meaning that you can use it from a HTML or text template the following way:

```html
<a href="{{ self.link_html }}">
    Click here to display this email in a browser
</a>
```

```{note}
The {py:attr}`~.wailer.models.Email.link_html` and
{py:attr}`~.wailer.models.Email.link_text` attributes are not absolute URLs.
Here we rely on Wailer's ability to automatically transform relative URLs into
absolute ones in HTML templates in order for this link to work.
```

### Attachments

If you want to add attachments to the email, you can override the 
{py:meth}`~.wailer.interfaces.EmailType.get_attachments` method and return the
list of attachments to be added.

Attachments have to be fitting into memory, and as a general rule most of email
providers will not allow attachments of more than 10 Mio.

Here is a simple example of how to add an attachment, by implementing 
{py:meth}`~.wailer.interfaces.EmailType.get_attachments`:

```python
    def get_attachments(self) -> Iterable[EmailAttachment]:
        return [EmailAttachment("hello.txt", b"\x00\x01\x02", "application/octet-stream")]
```

## Conclusion

We've seen that in order to provide you protection against common emailing
pitfalls, Wailer will ask you to write your emails through the implementation
of a given interface.

This will bring you to focus on providing the business rules while the emailing
mechanics are managed by the library itself. It comes at the price of a bit of
rigidity but the author of this library believes that it is totally worth the
effort.

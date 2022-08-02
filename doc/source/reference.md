# API Reference

That section is not didactic at all, just listing the documentation of every
bit of code for a complete reference.

## Template tags

Adding `{% load wailer %}` in your template will provide you with different
tags that can be helpful in the context of emails.

### `email_style`

In order to load some CSS in a HTML template, you may invoke the `email_style`
template. This will look for this specified CSS file in your static files
and will inline it inside the HTML.

**my_app/static/style.css**

```css
h1 {
    color: red;
}
```

**my_app/templates/template.html**

```html
{% load wailer %}

{% email_style "style.css" %}

<h1>Title</h1>
```

```{note}
Style files are resolved using Django's static files system
```

### `make_absolute`

In order to make an URL absolute, you can use this tag which will prepend the
URL with the website's domain. You can check how the domain is determined in
the [tutorial](absolute_url).

```html
{% load wailer %}

{% make_absolute "/foo/bar" %}
<!-- Will output "https://my-app.com/foo/bar -->
```

### `absolute_url`

Works _exactly_ like Django's
[url](https://docs.djangoproject.com/en/4.0/ref/templates/builtins/#url)
template tag with the only difference being the fact that all URLs generated
will be absolute. The domain name of those URLs will be determined in the way
that is explained in the [tutorial](absolute_url).

```html
{% load wailer %}

{% url "product_page" product.id %}
<!-- Instead of /product/42/ will output https://my-app.com/product/42/ -->
```

## Models

Those Django models are the core of the system. They both store the data in
database and perform the various plumbing tasks, including actually sending
messages.

### Base Message

Since emails and SMSes are very similar concept, this base class will hold
common concepts between the two, letting them specialize only on some core
aspects.

```{eval-rst}
.. autoclass:: wailer.models.BaseMessage
   :members:
```

### Email

Specialization of the base message to be able to send emails.

```{eval-rst}
.. autoclass:: wailer.models.Email
   :members:
```

## Interfaces

Those interfaces help you implement your own custom behaviors.

### SMS/Email common class

```{eval-rst}
.. autoclass:: wailer.interfaces.BaseMessageType
   :members:
```

### Email types

```{eval-rst}
.. autoclass:: wailer.interfaces.EmailType
   :members:
```

## Type aliases

Those are type aliases that are used throughout the app for clarity.

### JSON Type

This one mimics the JSON spec to indicate that this value should be matching
concepts that exist in JSON.

```{eval-rst}
.. autodata:: wailer.interfaces.JsonType
   :annotation: Represents a JSON-serializable type
```

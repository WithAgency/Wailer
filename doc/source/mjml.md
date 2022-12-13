# MJML

Wailer supports out-of-the box [MJML](https://mjml.io/) templates.

It's a markup language specifically made for emails. It allows you to generate
complex email components in a very simple way.

## Usage

If you want to take advantage of MJML, all you need to do is give the `.mjml`
extension to your template file (instead of `.html`). This will automatically
trigger a different build process. It will, in that order:

1. Render the `.mjml` file through the Django template engine
2. Render the output through MJML
3. Render the output through Premailer to transform relative URLs into absolute
   ones

Typically, you can write templates like this:

```mjml
{% load i18n %}
<mjml>
    <mj-head>
        <mj-attributes>
            <mj-text padding="0" />
            <mj-all font-family="Helvetica, Arial" />
        </mj-attributes>
    </mj-head>
    <mj-body>
        <mj-hero>
            <mj-text>
                {% blocktrans %}Hello, {{ name }}!{% endblocktrans %}
            </mj-text>
        </mj-hero>
    </mj-body>
</mjml>
```

```{note}
Let's note that MJML has its own styling system, so don't try to import a style
tag from a CSS file. It won't work. You need to use the MJML syntax.
```

## Caveats

MJML is a node library. In order to use it, it is installed on-the-fly when you
invoke a MJML rendering. This is less-than-perfect, but it works. However it
means that:

-   If you run the code on a server that can't access NPM, it won't work
-   The rendering of emails is a bit slow. It's recommended that you do it from
    a background task (like a Celery task) so that it doesn't block the user

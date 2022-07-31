# Installation

In order to install Wailer, you need to go through a few steps.

## Add to dependencies

Add `wailer` to your dependencies. It respects Semver and takes a commitment to
not produce breaking changes unless it is really worth it. Ideally it won't 
break anything for the next 10 years once past the version 1.0.

## Alter settings

First step is to add `wailer` to your installed apps:

```python
INSTALLED_APPS = [
    # ...
    "wailer",
    # ...
]
```

Then create at least this setting:

```python
WAILER_EMAIL_TYPES = {
}
```

More settings are available, you'll figure them in the next section.

## Add to URLs

Finally, import Wailer's URLs into your project:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("wailer/", include("wailer.urls")),
    # ...
]
```

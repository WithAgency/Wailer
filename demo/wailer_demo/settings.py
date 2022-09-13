"""
Django settings for wailer_demo project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path

from model_w.env_manager import EnvManager

with EnvManager() as env:
    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = "django-insecure-x533(^)hyw%66smxs@@x3o2t7vup)su1@!*l+y!i0vr+r9izg4"

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    ALLOWED_HOSTS = []

    # Application definition

    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.sites",
        "wailer",
        "my_app",
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]

    ROOT_URLCONF = "wailer_demo.urls"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ]

    WSGI_APPLICATION = "wailer_demo.wsgi.application"

    # Database
    # https://docs.djangoproject.com/en/4.0/ref/settings/#databases

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

    # Password validation
    # https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

    AUTH_USER_MODEL = "my_app.User"

    # Internationalization
    # https://docs.djangoproject.com/en/4.0/topics/i18n/

    LANGUAGE_CODE = "en"

    LANGUAGES = [
        ("en", "English"),
        ("fr", "French"),
    ]

    LOCALE_PATHS = [BASE_DIR / "locales"]

    TIME_ZONE = "UTC"

    USE_I18N = True

    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/4.0/howto/static-files/

    STATIC_URL = "static/"

    # Default primary key field type
    # https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    # ---
    # Sites framework
    # ---

    SITE_ID = 1

    # ---
    # Wailer
    # ---

    WAILER_EMAIL_TYPES = {
        "static": "my_app.emails.Static",
        "static-no-text": "my_app.emails.StaticNoText",
        "static-no-html": "my_app.emails.StaticNoHtml",
        "hello": "my_app.emails.Hello",
        "hello-user": "my_app.emails.HelloUser",
        "styled-html": "my_app.emails.StyledHtml",
        "absolute-url-straight": "my_app.emails.AbsoluteUrlStraight",
        "absolute-url-as": "my_app.emails.AbsoluteUrlAs",
        "make-absolute": "my_app.emails.MakeAbsolute",
    }

    WAILER_SMS_TYPES = {
        "hello": "my_app.sms.Hello",
        "hello-user": "my_app.sms.HelloUser",
    }

    # ---
    # Emails
    # ---

    _email_mode = env.get("EMAIL_MODE", default="console")

    if _email_mode == "mailjet":
        EMAIL_BACKEND = "wailer.backends.MailjetEmailBackend"
        MAILJET_API_KEY_PUBLIC = env.get("MAILJET_API_KEY_PUBLIC")
        MAILJET_API_KEY_PRIVATE = env.get("MAILJET_API_KEY_PRIVATE")
    else:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

    # ---
    # SMS
    # ---

    _sms_mode = env.get("SMS_MODE", default="console")

    if _sms_mode == "mailjet":
        SMS_BACKEND = "wailer.backends.MailjetSmsBackend"
        MAILJET_API_TOKEN = env.get("MAILJET_API_TOKEN")
    else:
        SMS_BACKEND = "sms.backends.console.SmsBackend"

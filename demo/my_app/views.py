from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest) -> HttpResponse:  # pragma: no coverage
    """
    A fake empty view that just needs to exist so we can generate reverse URLs
    on it (for testing purposes).
    """

    return HttpResponse(b"")

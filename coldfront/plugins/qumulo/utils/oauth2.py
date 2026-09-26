from django.http import JsonResponse
from oauth2_provider.views.mixins import OAuthLibMixin


class SessionOrOAuth2RequiredMixin(OAuthLibMixin):
    """
    Allows a view to be called either by a logged-in browser session (the
    existing session-cookie flow) or by a machine client presenting a
    Bearer token obtained via the OAuth2 client_credentials grant.

    Set `required_scopes` on the subclass to restrict which token scopes are
    accepted; an empty list (the default) accepts any valid token.
    """

    required_scopes = []

    def get_scopes(self):
        return self.required_scopes

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        valid, oauthlib_req = self.verify_request(request)
        if not valid:
            return JsonResponse(
                {
                    "detail": (
                        "Authentication credentials were not provided or are "
                        "invalid. Log in with a session cookie or supply a "
                        "valid 'Authorization: Bearer <token>' header."
                    )
                },
                status=401,
            )

        request.resource_owner = oauthlib_req.user
        request.access_token = oauthlib_req.access_token
        request.client = oauthlib_req.client

        return super().dispatch(request, *args, **kwargs)

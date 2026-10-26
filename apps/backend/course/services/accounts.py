from allauth.account.adapter import DefaultAccountAdapter


class InvitationAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # Invitation acceptance is the sole local provisioning endpoint.
        return False

from mindbox.models import CorporateEmailDomain


def is_corporate_email(email: str) -> bool:
    domain = email.lower().split("@")[-1]
    return CorporateEmailDomain.objects.filter(domain=domain).exists()

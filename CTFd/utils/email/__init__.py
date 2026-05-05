from flask import url_for

from CTFd.constants.email import (
    DEFAULT_PASSWORD_CHANGE_ALERT_BODY,
    DEFAULT_PASSWORD_CHANGE_ALERT_SUBJECT,
    DEFAULT_PASSWORD_RESET_BODY,
    DEFAULT_PASSWORD_RESET_SUBJECT,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
    DEFAULT_USER_CREATION_EMAIL_BODY,
    DEFAULT_USER_CREATION_EMAIL_SUBJECT,
    DEFAULT_VERIFICATION_EMAIL_BODY,
    DEFAULT_VERIFICATION_EMAIL_SUBJECT,
    DEFAULT_WINNER_CERTIFICATE_SUBJECT,
    DEFAULT_WINNER_CERTIFICATE_BODY,
)
from CTFd.utils import get_config
from CTFd.utils.config import get_mail_provider
from CTFd.utils.email.providers.mailgun import MailgunEmailProvider
from CTFd.utils.email.providers.smtp import SMTPEmailProvider
from CTFd.utils.formatters import safe_format
from CTFd.utils.security.email import (
    generate_email_confirm_token,
    generate_password_reset_token,
)

PROVIDERS = {"smtp": SMTPEmailProvider, "mailgun": MailgunEmailProvider}


def sendmail(addr, text, subject="Message from {ctf_name}", attachment=None):
    subject = safe_format(subject, ctf_name=get_config("ctf_name"))
    provider = get_mail_provider()
    EmailProvider = PROVIDERS.get(provider)
    if EmailProvider is None:
        return False, "No mail settings configured"
    return EmailProvider.sendmail(addr, text, subject, attachment=attachment)
    


def password_change_alert(email):
    text = safe_format(
        get_config("password_change_alert_body") or DEFAULT_PASSWORD_CHANGE_ALERT_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("auth.reset_password", _external=True),
    )

    subject = safe_format(
        get_config("password_change_alert_subject")
        or DEFAULT_PASSWORD_CHANGE_ALERT_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=email, text=text, subject=subject)


def forgot_password(email):
    text = safe_format(
        get_config("password_reset_body") or DEFAULT_PASSWORD_RESET_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for(
            "auth.reset_password",
            data=generate_password_reset_token(email),
            _external=True,
        ),
    )

    subject = safe_format(
        get_config("password_reset_subject") or DEFAULT_PASSWORD_RESET_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=email, text=text, subject=subject)


def verify_email_address(addr):
    text = safe_format(
        get_config("verification_email_body") or DEFAULT_VERIFICATION_EMAIL_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for(
            "auth.confirm",
            data=generate_email_confirm_token(addr),
            _external=True,
            _method="GET",
        ),
    )

    subject = safe_format(
        get_config("verification_email_subject") or DEFAULT_VERIFICATION_EMAIL_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=addr, text=text, subject=subject)


def successful_registration_notification(addr):
    text = safe_format(
        get_config("successful_registration_email_body")
        or DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("views.static_html", _external=True),
    )

    subject = safe_format(
        get_config("successful_registration_email_subject")
        or DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=addr, text=text, subject=subject)


def user_created_notification(addr, name, password):
    text = safe_format(
        get_config("user_creation_email_body") or DEFAULT_USER_CREATION_EMAIL_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("views.static_html", _external=True),
        name=name,
        password=password,
    )

    subject = safe_format(
        get_config("user_creation_email_subject")
        or DEFAULT_USER_CREATION_EMAIL_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=addr, text=text, subject=subject)

def winner_certificate(addr, name, rank, score):
    from CTFd.plugins.certificate_generator.utils import generate_winner_certificate
    import os

    ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
    rank_label = ordinals.get(rank, f"{rank}th")
    ctf_name = get_config("ctf_name")

    subject = f"Congratulations from {ctf_name}!"

    text = (
        f"Congratulations {name}!\n\n"
        f"You finished in {rank_label} place "
        f"with a final score of {score} points in {ctf_name}.\n\n"
        "Please find your winner certificate attached. Well done!"
    )
    try:
        cert_path = generate_winner_certificate(name, rank)
    except Exception as e:
        print(f"[winner_certificate] Failed to generate certificate: {e}", flush=True)
        cert_path = None

    result = sendmail(addr=addr, text=text, subject=subject, attachment=cert_path)

    # Clean up the temp file after sending
    if cert_path and os.path.isfile(cert_path):
        try:
            os.remove(cert_path)
        except Exception:
            pass

    print("[winner_certificate] SENDMAIL RESULT:", result, flush=True)
    return result

def check_email_is_whitelisted(email_address):
    local_id, _, domain = email_address.partition("@")
    domain_whitelist = get_config("domain_whitelist")

    if domain_whitelist:
        domain_whitelist = [d.strip() for d in domain_whitelist.split(",")]

        for allowed_domain in domain_whitelist:
            if allowed_domain.startswith("*."):
                # domains should never container the "*" char
                if "*" in domain:
                    return False

                # Handle wildcard domain case
                suffix = allowed_domain[1:]  # Remove the "*" prefix
                if domain.endswith(suffix):
                    return True

            elif domain == allowed_domain:
                return True

        # whitelist is specified but the email doesn't match any domains
        return False

    # whitelist is not specified - allow all emails
    return True


def check_email_is_blacklisted(email_address):
    local_id, _, domain = email_address.partition("@")
    domain_blacklist = get_config("domain_blacklist")

    if domain_blacklist:
        domain_blacklist = [d.strip() for d in domain_blacklist.split(",")]

        for disallowed_domain in domain_blacklist:
            if disallowed_domain.startswith("*."):
                # domains should never container the "*" char
                if "*" in domain:
                    return True

                # Handle wildcard domain case
                suffix = disallowed_domain[1:]  # Remove the "*" prefix
                if domain.endswith(suffix):
                    return True

            elif domain == disallowed_domain:
                return True

        # blacklist is specified but the email is not blacklisted
        return False

    # blacklist is not specified - no emails are blacklisted
    return False

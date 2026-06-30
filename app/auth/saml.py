from urllib.parse import urlparse

from flask import current_app, request


def saml_available():
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth  # noqa: F401
        from onelogin.saml2.settings import OneLogin_Saml2_Settings  # noqa: F401
    except ImportError:
        return False

    return True


def saml_enabled():
    return current_app.config["SAML_ENABLED"] and saml_available()


def saml_settings():
    return {
        "strict": current_app.config["SAML_STRICT"],
        "debug": current_app.config["SAML_DEBUG"],
        "sp": {
            "entityId": current_app.config["SAML_SP_ENTITY_ID"],
            "assertionConsumerService": {
                "url": current_app.config["SAML_SP_ACS_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": current_app.config["SAML_SP_SLS_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": "",
            "privateKey": "",
        },
        "idp": {
            "entityId": current_app.config["SAML_IDP_ENTITY_ID"],
            "singleSignOnService": {
                "url": current_app.config["SAML_IDP_SSO_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": current_app.config["SAML_IDP_SLO_URL"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": current_app.config["SAML_IDP_X509_CERT"],
        },
    }


def _prepare_request_data():
    url_data = urlparse(request.url)
    return {
        "https": "on" if request.is_secure else "off",
        "http_host": request.host,
        "server_port": url_data.port or ("443" if request.is_secure else "80"),
        "script_name": request.path,
        "get_data": request.args.copy(),
        "post_data": request.form.copy(),
        "query_string": request.query_string,
    }


def build_saml_auth():
    from onelogin.saml2.auth import OneLogin_Saml2_Auth

    return OneLogin_Saml2_Auth(_prepare_request_data(), old_settings=saml_settings())


def saml_metadata():
    from onelogin.saml2.settings import OneLogin_Saml2_Settings

    settings = OneLogin_Saml2_Settings(settings=saml_settings(), custom_base_path=None)
    return settings.get_sp_metadata()

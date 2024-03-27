from django.utils.translation import gettext_lazy as _

COOKIEBANNER = {
    "title": _("Cookie Einstellungen"),
    "header_text": _("Diese Website verwendet Cookies."),
    "footer_links": [
        {"title": _("Impressum"), "href": "/imprint"},
        {"title": _("Datenschutz"), "href": "/privacy"},
    ],
    "groups": [
        {
            "id": "essential",
            "name": _("Notwendig"),
            "description": _("Notwendige Cookies sind nötig um die Seite zu verwenden."),
            "cookies": [
                {
                    "pattern": "cookiebanner",
                    "description": _("Meta Cookie zum speichern der Cookie Einstellungen."),
                },
                {
                    "pattern": "csrftoken",
                    "description": _("Dieser Cookie verhindert Cross-Site-Request-Forgery Angriffe."),
                },
                {
                    "pattern": "sessionid",
                    "description": _("Dieser Cookie ist notwendig um Anmelden möglich zu machen."),
                }
            ],
        },
        {
            "id": "theme",
            "name": _("Farbschema (Optional)"),
            "optional": True,
            "cookies": [
                {
                    "pattern": "theme",
                    "description": _("Dieser Cookie wird verwendet um das Farbschema der Website zu speichern."),
                },
            ],
        },
    ],
}

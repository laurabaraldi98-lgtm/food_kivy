TEXTS = {
    "it": {
        "home_title": "Cosa mangiamo?",
        "choose_for_me": "Scegli per me",
        "no_active_list": "Nessuna lista attiva",
        "active_list": "Lista attiva: {name}",
        "manage_lists": "Gestisci liste",
        "logout": "Logout",
        "create_list_first": "Crea prima una lista",
        "add_food_first": "Aggiungi prima qualche cibo",
        "language": "Lingua",
        "sign_in": "Accedi",
        "forgot_password": "Password dimenticata?",
        "no_account": "Non hai ancora un account?",
        "create_one": "Creane uno",
        "email_password_required": "Inserisci email e password",
        "invalid_credentials": "Email o password non corretti",
        "email_required_for_reset": "Inserisci prima la tua email",
        "reset_request_failed": "Impossibile inviare l'email di recupero",
        "reset_email_sent": (
            "Controlla la tua email per reimpostare la password"
        ),
    },
    "en": {
        "home_title": "What should we eat?",
        "choose_for_me": "Choose for me",
        "no_active_list": "No active list",
        "active_list": "Active list: {name}",
        "manage_lists": "Manage lists",
        "logout": "Log out",
        "create_list_first": "Create a list first",
        "add_food_first": "Add some food first",
        "language": "Language",
        "sign_in": "Sign in",
        "forgot_password": "Forgot password?",
        "no_account": "Don't have an account?",
        "create_one": "Create one",
        "email_password_required": "Enter email and password",
        "invalid_credentials": "Incorrect email or password",
        "email_required_for_reset": "Enter your email first",
        "reset_request_failed": "Could not send the reset email",
        "reset_email_sent": "Check your email to reset your password",
    },
}


def translate(language, key, **values):
    return TEXTS[language][key].format(**values)

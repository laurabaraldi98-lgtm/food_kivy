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
    },
}


def translate(language, key, **values):
    return TEXTS[language][key].format(**values)

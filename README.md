# Food App

[![Python tests](https://github.com/laurabaraldi98-lgtm/food_kivy/actions/workflows/tests.yml/badge.svg)](https://github.com/laurabaraldi98-lgtm/food_kivy/actions/workflows/tests.yml)

A responsive food suggestion application built with Python and Kivy for desktop
and Android.

Food App helps users decide what to eat by selecting a random item from one of
their food lists. Users can create personal lists or share lists with other
registered users. Food data is stored remotely in Supabase and protected with
PostgreSQL Row Level Security.

The application supports persistent login. Refresh tokens are stored using the
operating system's secure credential storage on desktop and Android Keystore on
Android.

The interface is available in Italian and English. Users can change language
from the login and registration screens or from the application menus. The
choice is saved on the device. List names and food names entered by users are
never translated automatically.

---

## Screenshots

The screenshots below show the Italian interface.

|                                   Login                                   |                                  Home                                   |
| :-----------------------------------------------------------------------: | :---------------------------------------------------------------------: |
| <img src="screenshots/login.png" alt="Food App login screen" width="320"> | <img src="screenshots/home.png" alt="Food App home screen" width="320"> |

|                                Personal and shared lists                                |                                Food management                                 |
| :-------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------: |
| <img src="screenshots/food-lists.png" alt="Personal and shared food lists" width="320"> | <img src="screenshots/food-popup.png" alt="Food management popup" width="320"> |

---

## Why I Built This

This project started from a very common problem: deciding what to eat.

The same question kept coming up:

> "What should we have for dinner?"

Usually followed by:

> "I don't know."

Instead of spending time trying to decide, I built a small application that
makes the choice automatically.

The original idea was intentionally simple: keep a list of foods you actually
eat, press a button, and let the app select one.

What began as a local Python project gradually evolved into a cross-platform
application involving:

- a responsive graphical interface;
- remote data persistence;
- REST API communication;
- user authentication and persistent sessions;
- personal and shared data;
- PostgreSQL Row Level Security;
- secure credential storage;
- an Italian and English interface;
- Android packaging;
- automated testing;
- continuous integration.

---

## Features

### Authentication

- User registration with email and password
- Email confirmation through Supabase
- User login and logout
- Password reset by email
- Authenticated API requests using access tokens
- Persistent login after closing and reopening the application
- Refresh-token rotation when the session is renewed
- Automatic access-token renewal before an authenticated request when needed
- Secure refresh-token storage on desktop and Android
- Local session cleanup when a refresh token is rejected

### Personal food lists

- Default list containing 22 foods for every new user
- Multiple personal lists
- Create, select, rename, and delete lists
- Separate foods for every list
- Automatic selection of an available list after login
- Clear indication of the currently active list

### Shared food lists

- Create a list shared with other registered users
- Add members by email address
- View the members of a shared list
- Remove members from a shared list
- Shared access to the same foods
- Owner and member roles
- Members can leave a shared list
- Only the owner can delete a shared list

### Food management

- View all foods in the active list
- Add foods
- Remove foods
- Case-insensitive duplicate detection
- Random food selection
- Immediate persistence in Supabase
- Shared changes visible to every authorized member

### Interface and languages

- Italian and English interface text
- Language controls on the login and registration screens
- Language controls in the home and food-list menus
- Custom flag images for the language controls
- Language preference saved locally and restored after restarting the
  application
- User-entered list names and food names preserved in their original language
- Responsive Kivy layouts
- Reusable rounded buttons
- Custom hamburger menu button
- Scrollable food-list screen
- Scrollable food-management popup
- One input field for adding and deleting foods
- Side-by-side add and delete buttons
- Density-independent dimensions with `dp`
- Scalable text sizes with `sp`
- Adaptive backgrounds
- Android software-keyboard handling
- Custom font, illustrations, and application icon
- Desktop and Android support

### Testing and automation

- Automated tests for application behaviour and both interface languages
- A 100% statement-coverage requirement for the Python modules measured in CI
- Tests for secure-storage integration without accessing real credentials
- GitHub Actions CI on pushes and pull requests
- Headless Kivy testing with Xvfb
- Android APK build workflow
- Versioned PostgreSQL migrations

---

## How It Works

When the application starts, it loads the saved language preference and looks
for a saved refresh token in the device's secure credential storage.

If a token is available, the application asks Supabase to renew the session and
opens the food screen. Otherwise, it displays the login screen.

Users can:

- change the interface language;
- sign in with an existing account;
- open the registration screen;
- request a password-reset email.

New accounts can receive a confirmation email through Supabase. Authentication
redirects are handled by pages hosted with GitHub Pages:

```text
https://laurabaraldi98-lgtm.github.io/food_kivy/
```

After a successful login, Supabase returns a session containing an access token
and a refresh token.

The access token is used for authenticated requests. The refresh token is saved
in the device's secure credential storage so the application can restore the
session after a restart.

When the application renews a session, Supabase returns a new refresh token. The
application replaces the previously saved token with the new one. Renewal
happens when the application reopens or when a protected request needs a fresh
access token; it does not run continuously in the background.

The application loads the food lists available to the authenticated user. If at
least one list exists, the first available list becomes active automatically.

The user can then:

1. open the list-management screen;
2. create or select a list;
3. add or remove foods;
4. return to the home screen;
5. press **Scegli per me** or **Choose for me**;
6. receive a randomly selected food from the active list.

Changes are sent immediately to Supabase, so lists and foods remain available
after the application is closed.

Selecting logout clears the saved refresh token and application state, then
returns the user to the login screen. The application also requests server-side
sign-out when it can reach Supabase.

---

## Persistent Login and Token Storage

`session_storage.py` provides the same save, load, and delete operations to the
rest of the application while selecting the storage implementation for the
current platform.

On desktop, `desktop_token_store.py` uses `keyring` to access a supported
operating-system credential store:

- Windows Credential Manager on Windows;
- Keychain on macOS;
- a supported Secret Service or KWallet backend on Linux.

On Android, `android_token_store.py` uses PyJNIus to call `TokenVault.java`. The
Java class uses Android Keystore for the encryption key and stores the encrypted
refresh token in application-private preferences.

If secure storage is unavailable, the application does not save the refresh
token in plaintext. The user may need to sign in again after restarting the
application.

Older versions stored the refresh token in a local `session.json` file. When
that file is encountered, the application attempts to move its token to secure
storage and removes the old plaintext file. If the migration cannot be completed
securely, the old file is removed and the user must sign in again.

Tests replace the operating-system storage with in-memory fakes. They do not
read or modify a developer's real saved credentials.

---

## Language Settings

`translations.py` contains the Italian and English interface strings. Screens
and popups request a string by its key, then display it in the selected
language.

`language_settings.py` saves the selected language in the application's local
data directory. The preference is restored when the application starts again.
Unlike a refresh token, the language setting is not a secret and does not
require encrypted storage.

The language controls appear on the login and registration screens, as well as
in the home and food-list menus. Switching languages updates the application's
interface text. A popup opened after the change uses the selected language.

Only interface text is translated. For example, a list named `Cena` remains
`Cena` when the interface is switched to English. Food names, list names, and
email addresses are treated as user data.

---

## Personal and Shared Lists

### Personal lists

A personal list belongs to one user through its `owner_id`.

Only its owner can:

- view it;
- rename it;
- delete it;
- view its foods;
- add foods;
- remove foods.

### Shared lists

A shared list is connected to an internal group through its `group_id`.

Groups do not have a separate screen in the application. Users interact directly
with personal and shared lists from the same list-management screen.

When a shared list is created:

1. the application creates a group;
2. the creator becomes its owner;
3. the owner is added automatically as a group member;
4. the food list is connected to the group;
5. the owner can add registered users by email.

The permissions are:

| Action                       | Owner | Member |
| ---------------------------- | :---: | :----: |
| View the shared list         |  Yes  |  Yes   |
| View its foods               |  Yes  |  Yes   |
| Add and remove foods         |  Yes  |  Yes   |
| Rename the list              |  Yes  |  Yes   |
| View members                 |  Yes  |  Yes   |
| Add members                  |  Yes  |   No   |
| Remove other members         |  Yes  |   No   |
| Leave the list               |  No   |  Yes   |
| Delete the list for everyone |  Yes  |   No   |

A regular member can leave without deleting the list for the remaining users.

Deleting a shared list removes its foods, memberships, and internal group
through PostgreSQL cascade rules.

The owner cannot currently leave or transfer ownership. Ownership transfer may
be implemented in a future version.

---

## Application Structure

Responsibilities are separated across multiple modules:

- `main.py` manages application state, session renewal, the active list,
  language changes, and screen navigation;
- `auth_client.py` communicates with Supabase Authentication;
- `session_storage.py` selects secure token storage and handles migration from
  the older local file;
- `desktop_token_store.py` uses supported desktop credential stores through
  `keyring`;
- `android_token_store.py` connects Python to the Android Java implementation
  through PyJNIus;
- `android_src/org/foodkivy/security/TokenVault.java` encrypts and stores the
  token on Android;
- `supabase_client.py` communicates with the Supabase REST API;
- `auth_screen.py` implements login and password reset;
- `signup_screen.py` implements registration;
- `food_lists_screen.py` manages personal and shared lists;
- `food_list_popups.py` contains the list creation, rename, delete, and leave
  popups;
- `food_popup.py` manages foods inside the active list;
- `group_members_popup.py` manages shared-list members;
- `translations.py` contains the Italian and English interface strings;
- `language_settings.py` saves and loads the language preference;
- `ui_components.py` contains reusable Kivy widgets.

The application uses standard HTTP requests instead of the full Supabase Python
SDK.

This keeps the Android dependency tree smaller and avoids transitive packages
that are difficult to cross-compile with python-for-android.

---

## Supabase REST Integration

The REST endpoints are built from the Supabase project URL.

For example:

```python
FOODS_URL = f"{SUPABASE_URL}/rest/v1/foods"
```

Protected requests include the authenticated user's access token:

```python
headers["Authorization"] = f"Bearer {access_token}"
```

The application uses:

- `GET` to retrieve lists, foods, groups, and members;
- `POST` to create records and call PostgreSQL functions;
- `PATCH` to rename lists and groups;
- `DELETE` to remove foods, lists, groups, and memberships;
- RPC endpoints for protected membership operations.

The access token identifies the current user. Database policies then determine
which records that user is allowed to access.

---

## Database Model

The main PostgreSQL tables are:

- `default_foods` — template used to populate a new user's default list;
- `food_lists` — personal and shared lists;
- `foods` — food items connected to lists through `list_id`;
- `groups` — internal ownership records for shared lists;
- `group_members` — users allowed to access shared lists.

A personal list has an `owner_id`.

A shared list has a `group_id`.

A database constraint ensures that a list belongs either to one user or to one
group, never both.

The `group_members` table stores the user's role:

- `owner`;
- `member`.

When a group is created, a PostgreSQL trigger automatically inserts its creator
into `group_members` as the owner.

Database functions support authorization and membership management, including:

- checking whether a user belongs to a group;
- checking whether a user owns a group;
- checking access to a food list;
- retrieving group members;
- adding an existing user by email.

---

## Database Security

Row Level Security is enabled for application data.

The database policies enforce the following rules:

- anonymous users cannot access food data;
- users can access only their own personal lists;
- users can access shared lists only when they belong to the corresponding
  group;
- group members can view and modify foods in an accessible shared list;
- only the owner can add other members;
- only the owner can remove other members;
- members cannot add themselves to arbitrary groups;
- regular members can remove only their own membership when leaving;
- the owner's membership cannot be removed;
- only the owner can delete a shared list and its group.

These permissions are enforced in PostgreSQL, not only by hiding buttons in the
interface.

The application uses the Supabase publishable key or legacy `anon` key together
with the authenticated user's access token.

The `service_role` key must never be included in the client application.

The SQL schema, policies, functions, and triggers are stored as versioned
migrations in:

```text
supabase/migrations/
```

---

## User Interface

The application uses a Kivy `ScreenManager` to navigate between:

- the login screen;
- the registration screen;
- the main food screen;
- the food-list management screen.

### Main screen

The main screen displays:

- the active food list;
- the random-choice button;
- the randomly selected result;
- the hamburger navigation button.

If no list is active, the user is asked to create one.

If the active list is empty, the user is asked to add foods first.

### Food-list screen

The list-management screen displays personal and shared lists together.

Shared lists are marked with `(condivisa)` in Italian or `(shared)` in English.
The list name itself stays as the user entered it.

Selecting a list reveals its available actions.

A shared-list owner sees the delete action, while a regular member sees the
option to leave the list.

### Food-management popup

The food-management popup contains:

- a scrollable list of foods;
- one text field;
- buttons to add and delete foods;
- status feedback.

The same input is used for both adding and deleting a food. The two action
buttons are displayed side by side and use the reusable `RoundedButton`
component.

### Member-management popup

The member popup displays every user who can access a shared list.

All members can view the participants. Only the owner sees the controls for
adding or removing other members.

Duplicate memberships are rejected.

### Reusable components

`RoundedButton` draws its background with a Kivy `RoundedRectangle`.

`MenuButton` extends it and draws the hamburger icon using three canvas lines,
so the icon does not depend on a special font character.

---

## Responsive Design

Desktop and Android devices can have very different:

- resolutions;
- pixel densities;
- physical dimensions;
- aspect ratios.

Raw pixel values caused controls to appear at inconsistent physical sizes.

The interface therefore uses:

- `dp` for widget dimensions, spacing, padding, and rounded corners;
- `sp` for text sizes;
- `size_hint` for proportional sizing;
- `pos_hint` for proportional positioning;
- scrollable layouts for content that may exceed the available space.

For example:

```python
self.choose_button.height = dp(48)
self.title_label.font_size = sp(34)
```

---

## Adaptive Backgrounds

Background images use:

```python
fit_mode="cover"
```

This fills the available screen without stretching the illustration.

However, the same image can be cropped differently on tall mobile displays.

The home screen therefore calculates the current aspect ratio:

```python
ratio = Window.width / Window.height
```

It then selects the appropriate asset:

```python
background_source = (
    "images/background_tall.png"
    if ratio < 0.48
    else "images/background.png"
)
```

Tall screens use `background_tall.png`, while standard displays use
`background.png`.

---

## Mobile Keyboard Handling

On Android, the software keyboard can cover form controls.

The application uses:

```python
Window.softinput_mode = "below_target"
```

When the food input receives focus, the popup scrolls toward the field so that
the input and buttons remain visible.

The focus handler runs only on Android:

```python
if platform != "android" or not focused:
    return
```

This prevents the popup from moving unnecessarily when the field is selected on
desktop.

---

## Project Evolution

### 1. Local Python prototype

The original version stored foods in a local JSON file.

It focused on Python fundamentals, random selection, add and delete operations,
and simple persistence.

### 2. Kivy graphical interface

The project was converted into a graphical application using Kivy widgets,
layouts, labels, buttons, text inputs, popups, custom fonts, and image assets.

### 3. Supabase persistence

Local JSON food storage was replaced by a PostgreSQL database hosted on
Supabase.

This introduced remote persistence and REST API communication.

### 4. Android packaging

Buildozer and python-for-Android were introduced to package the project for
Android.

The Android application uses portrait orientation, Internet permission, a custom
icon, and a reduced dependency set.

### 5. Dependency redesign

The first Supabase implementation used the full Python SDK.

Some transitive dependencies were problematic to cross-compile for Android, so
the data and authentication layers were rewritten using direct `requests` calls.

### 6. Responsive redesign

Testing on physical Android devices revealed issues involving pixel density,
aspect ratios, background cropping, popup positioning, and the software
keyboard.

The interface was redesigned with `dp`, `sp`, adaptive images, proportional
positioning, and scrollable content.

### 7. Authentication and security

Supabase Authentication, email confirmation, password reset, access tokens,
protected requests, and PostgreSQL Row Level Security were added.

### 8. Multiple personal lists

The original single list evolved into multiple personal lists, including
automatic creation of a default list for every new user.

### 9. Shared lists

Shared lists introduced groups, memberships, roles, protected PostgreSQL
functions, database triggers, cascade deletion, and membership-based access
control.

Groups remain an internal database implementation rather than a separate concept
exposed in the interface.

### 10. Automated testing and CI

The test suite was expanded to cover HTTP clients, application state, Kivy
screens, popups, reusable components, personal lists, shared lists, membership
permissions, Android-specific behaviour, and error paths.

GitHub Actions requires 100% statement coverage for the selected Python modules.

### 11. Persistent login and secure token storage

The application now restores sessions after a restart and replaces saved refresh
tokens when Supabase renews them.

Refresh tokens are stored in supported desktop credential stores or encrypted
using Android Keystore. The older plaintext session file is removed during
migration.

The Android implementation was compiled into an APK and tested on a physical
phone for login persistence and logout.

### 12. Italian and English interface

Interface strings were moved into a shared translation table and connected to
the application's screens and popups.

Users can switch languages from the login and registration screens or from the
menus after signing in. The language choice is saved on the device, while list
names and food names remain unchanged.

---

## Technologies

### Application

- Python 3
- Kivy
- Requests
- `keyring` for desktop credential storage
- PyJNIus for Python-to-Java calls on Android
- Java for the Android Keystore integration

### Backend and data

- Supabase
- Supabase Authentication
- PostgreSQL
- Supabase REST API
- Row Level Security
- PostgreSQL functions and triggers
- SQL migrations

### Testing

- pytest
- pytest-cov
- `unittest.mock`
- Xvfb
- GitHub Actions

### Android

- Buildozer
- python-for-Android
- Android SDK
- Android NDK
- Android Keystore

### Web and development

- HTML
- CSS
- Git
- GitHub
- GitHub Pages

---

## Project Structure

```text
food_kivy/
├── .github/
│   └── workflows/
│       ├── build-apk.yml
│       └── tests.yml
├── android_src/
│   └── org/
│       └── foodkivy/
│           └── security/
│               └── TokenVault.java
├── docs/
│   └── index.html
├── fonts/
│   └── Pacifico-Regular.ttf
├── images/
│   ├── background.png
│   ├── background_tall.png
│   ├── flag_en.png
│   ├── flag_it.png
│   └── icon.png
├── screenshots/
│   ├── food-lists.png
│   ├── food-popup.png
│   ├── home.png
│   └── login.png
├── supabase/
│   ├── migrations/
│   │   ├── 20260908_initial_foods_schema.sql
│   │   ├── 20260909_enable_foods_rls.sql
│   │   ├── 20260912091103_create_food_lists.sql
│   │   ├── 20260912210221_allow_deleting_default_food_lists.sql
│   │   ├── 20260913132317_create_groups.sql
│   │   ├── 20260913133034_manage_group_members.sql
│   │   ├── 20260913134347_connect_groups_to_food_lists.sql
│   │   └── 20260913191848_restrict_group_member_management.sql
│   ├── .gitignore
│   └── config.toml
├── tests/
│   ├── food_lists_test_helpers.py
│   ├── test_android_token_store.py
│   ├── test_auth_client.py
│   ├── test_auth_screen.py
│   ├── test_desktop_token_store.py
│   ├── test_food_list_popups.py
│   ├── test_food_lists_screen.py
│   ├── test_food_popup.py
│   ├── test_group_members_popup.py
│   ├── test_language_settings.py
│   ├── test_language_ui.py
│   ├── test_main.py
│   ├── test_session_storage.py
│   ├── test_signup_screen.py
│   ├── test_supabase_client.py
│   └── test_ui_components.py
├── .gitignore
├── android_token_store.py
├── auth_client.py
├── auth_screen.py
├── buildozer.spec
├── desktop_token_store.py
├── food_list_popups.py
├── food_lists_screen.py
├── food_popup.py
├── group_members_popup.py
├── language_settings.py
├── main.py
├── make_flags.py
├── pytest.ini
├── session_storage.py
├── signup_screen.py
├── supabase_client.py
├── translations.py
├── ui_components.py
└── README.md
```

A local `config.py` file is also required, but it is excluded from Git because
it contains the Supabase project configuration.

---

## Configuration

Create `config.py` in the project root:

```python
SUPABASE_URL = "your-supabase-project-url"
SUPABASE_KEY = "your-supabase-publishable-or-anon-key"
```

Use the Supabase publishable key or legacy `anon` key.

Never place the `service_role` key inside the application.

`config.py` is included in `.gitignore` and must not be committed with real
project values.

---

## Run Locally

Clone the repository:

```bash
git clone https://github.com/laurabaraldi98-lgtm/food_kivy.git
cd food_kivy
```

Optionally create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the desktop dependencies:

```bash
python -m pip install kivy requests keyring pytest pytest-cov
```

Create `config.py` with the required Supabase values.

Run the application:

```bash
python main.py
```

Persistent login requires an available, supported operating-system credential
store. If secure storage is unavailable, the application can still run, but the
user may need to sign in again after closing it.

---

## Tests

Run the complete test suite:

```bash
python -m pytest
```

Run the tests with the same coverage requirement used by GitHub Actions:

```bash
python -m pytest --cov=auth_client --cov=android_token_store --cov=desktop_token_store --cov=auth_screen --cov=food_lists_screen --cov=food_list_popups --cov=food_popup --cov=group_members_popup --cov=language_settings --cov=main --cov=session_storage --cov=signup_screen --cov=supabase_client --cov=translations --cov=ui_components --cov-report=term-missing --cov-fail-under=100
```

GitHub Actions requires 100% statement coverage across the selected Python
modules.

These tests do not compile or execute `TokenVault.java`. The Android build
verifies compilation, and installation on a physical device verifies the login
and logout flow.

Tests run automatically on every push and pull request.

Xvfb provides a virtual display for Kivy tests on the GitHub Actions Ubuntu
runner.

---

## Android Build

Android packaging is configured in `buildozer.spec`.

The application requirements are:

```ini
requirements = python3,kivy,requests,certifi,urllib3,idna,charset_normalizer
```

The Android configuration includes:

```ini
orientation = portrait
android.permissions = INTERNET
android.api = 35
android.minapi = 24
android.ndk_api = 24
android.add_src = android_src
```

`android.add_src` includes the Java source that implements secure token storage
through Android Keystore.

The application icon is configured with:

```ini
icon.filename = images/icon.png
```

The **Build APK** GitHub Actions workflow runs automatically on pushes to
`main`. It can also be started manually for a selected branch using **Run
workflow**.

The Android APK has been tested on a physical phone for persistent login and
logout: the application retained the login after being closed and reopened, and
returned to the login screen after logout and reopening.

---

## Current Limitations

- Users must already have an account before they can be added to a shared list.
- There is no invitation flow for users without an account.
- Group ownership cannot currently be transferred.
- Database requests are synchronous.
- The application requires an Internet connection for remote data operations.
- Network errors have limited user-facing feedback.
- Offline caching and retry handling are not implemented.
- Persistent login depends on an available secure credential store on the
  device.
- Access tokens that have already been issued remain valid until their expiry
  even after the corresponding refresh token is revoked.

---

## Possible Future Improvements

- Shared-list invitations
- Group ownership transfer
- Improved loading indicators
- Better network-error feedback
- Asynchronous requests
- Retry handling
- Offline caching
- Synchronization after reconnecting
- Food categories
- Filters and favourites
- Additional languages
- Further animations and UI improvements

---

## What I Learned

This project provided practical experience with:

### Python and application structure

- separating responsibilities between modules;
- object-oriented programming and inheritance;
- application state management;
- reusable functions and UI components;
- external configuration;
- validation and exception handling;
- synchronization between local and remote state;
- managing interface translations and locally saved preferences.

### Kivy and Android

- widgets and layouts;
- screen navigation;
- popups and dropdown menus;
- canvas drawing;
- custom fonts and images;
- responsive design using `dp` and `sp`;
- scrollable mobile layouts;
- software-keyboard and focus handling;
- Buildozer and python-for-Android;
- Android dependency compatibility;
- APK creation and physical-device testing;
- calling Android Java APIs from Python through PyJNIus.

### APIs, databases, and security

- REST API communication;
- HTTP methods, headers, and JSON payloads;
- Supabase Authentication;
- access and refresh tokens;
- session renewal and refresh-token rotation;
- operating-system credential storage;
- Android Keystore;
- PostgreSQL relational modelling;
- foreign keys and cascade deletion;
- Row Level Security;
- membership-based authorization;
- PostgreSQL functions, triggers, constraints, and migrations.

### Testing and Git

- pytest and pytest-cov;
- mocking HTTP requests;
- patching application dependencies;
- testing Kivy widgets and nested callbacks;
- testing platform-specific behaviour;
- testing Italian and English interface behaviour;
- keeping tests isolated from real credentials;
- maintaining a 100% statement-coverage requirement;
- Git branches, commits, pull requests, and merges;
- GitHub Actions and automated builds.

---

## Status

The current version includes:

- registration, email confirmation, login, logout, and password reset;
- persistent login with secure refresh-token storage;
- automatic session renewal when needed;
- authenticated Supabase requests;
- multiple personal lists;
- default list creation with 22 foods;
- shared multi-user lists;
- owner and member permissions;
- member management by email;
- PostgreSQL Row Level Security;
- persistent remote data;
- random food selection;
- Italian and English interface text with a saved language preference;
- responsive desktop and Android layouts;
- custom application branding and language-control flag images;
- automated tests with a 100% statement-coverage requirement in CI.

The authentication flow, personal lists, shared lists, member management, and
food operations work on desktop. The persistent-login and logout flow has also
been verified on a physical Android phone.

# Food App

A responsive food suggestion app built with Python and Kivy for desktop and Android.

The app solves a simple everyday problem: deciding what to eat.

Users can create an account, sign in, maintain a list of foods, add or remove items, and let the app randomly choose one. The list is stored remotely in Supabase, so changes persist between sessions.

Supabase Authentication protects access to the application, while Row Level Security prevents anonymous users from accessing the food database.

The interface is currently in Italian.

---

## Why I Built This

This project started from a very common problem: deciding what to eat.

The same question kept coming up:

> "What should we have for dinner?"

Usually followed by:

> "I don't know."

Instead of spending time trying to decide, I built a small application that makes the choice automatically.

The original idea was intentionally simple: keep a list of foods you actually eat, press a button, and let the app pick one.

What began as a small Python project gradually evolved into a cross-platform application involving remote persistence, REST API communication, user authentication, database security, Android packaging, responsive UI design, mobile keyboard handling, automated tests, CI builds, and debugging across different physical devices.

---

## Features

- User registration with email and password
- Email confirmation through Supabase
- User login and logout
- Random food suggestion
- Add new foods
- Remove existing foods
- Persistent food list stored in Supabase
- Supabase REST API integration
- Authenticated database requests
- Row Level Security on the `foods` table
- Responsive Kivy interface
- Reusable rounded buttons and menu button
- Hamburger menu with logout action
- Density-independent widget sizing with `dp`
- Scalable font sizing with `sp`
- Desktop support
- Android support
- Portrait mobile layout
- Scrollable food-management popup
- Android soft-keyboard handling
- Adaptive background selection for different screen aspect ratios
- Custom application icon
- Custom font and graphical interface
- Italian-language UI
- Automated tests for the authentication and database clients

---

## How It Works

When the application starts, it displays the login screen.

Users can sign in with an existing account or open a separate registration screen to create a new one.

New accounts receive a confirmation email from Supabase. The confirmation link redirects to a small responsive page hosted with GitHub Pages:

```text
https://laurabaraldi98-lgtm.github.io/food_kivy/
```

After a successful login, Supabase returns a session containing an access token. The application stores the session while it is running and loads the current food list from the Supabase `foods` table.

Authentication logic is isolated in `auth_client.py`, while database communication is isolated in `supabase_client.py`.

Both clients use standard HTTP requests instead of the full Supabase Python SDK.

The food client performs three main operations:

- `GET` — retrieve the current food list
- `POST` — add a new food
- `DELETE` — remove an existing food

The REST endpoint is built from the Supabase project URL:

```python
BASE_URL = f"{SUPABASE_URL}/rest/v1/foods"
```

Every food request includes the user's access token:

```python
headers["Authorization"] = f"Bearer {access_token}"
```

When a food is added or deleted, the database is updated immediately. This means the list is still available after closing and reopening the app.

Selecting logout invalidates the Supabase session, clears the local session and food list, and returns the user to the login screen.

At the moment, all authenticated users still use the same shared food list. User-specific and group-shared lists will be implemented in a later development branch.

---

## Database Security

Row Level Security is enabled on the Supabase `foods` table.

The current database policies allow authenticated users to:

- read foods
- add foods
- delete foods

Anonymous requests cannot access the food list.

The SQL used to enable RLS and create the policies is recorded in:

```text
supabase/migrations/20260909_enable_foods_rls.sql
```

The current policies protect the database from anonymous access, but they do not yet separate data by user. All authenticated users can currently access the same foods.

A future database migration will connect foods to users and groups and replace the current policies with membership-based policies.

---

## User Interface

The application uses a Kivy `ScreenManager` to move between:

- login screen
- registration screen
- main food screen

The main screen contains two primary actions.

### Choose for me

The app randomly selects one food from the current list and displays the result.

### View food list

Opens the food-management popup where users can:

- view all saved foods
- add a new food
- remove an existing food

The popup also displays status feedback when an item is added, already exists, is removed, or cannot be found.

### Hamburger menu

A hamburger button in the upper-left corner opens a dropdown menu containing the logout action.

The reusable `RoundedButton` and `MenuButton` components are defined in `ui_components.py`.

The hamburger icon is drawn using three Kivy canvas lines, so it does not depend on a special font character.

---

## Responsive Design

A significant part of the project involved adapting the original Kivy interface to different devices.

Desktop and Android screens can have very different:

- resolutions
- pixel densities
- physical dimensions
- aspect ratios

Using fixed raw pixel values caused UI elements to appear at inconsistent sizes across devices.

The interface therefore uses Kivy's density-independent units.

### `dp`

`dp` is used for widget dimensions, spacing, padding, button heights, and rounded corners.

For example:

```python
self.choose_button.height = dp(52)
```

This helps controls maintain a more consistent physical size across displays with different pixel densities.

### `sp`

`sp` is used for text sizes.

For example:

```python
self.title_label.font_size = sp(34)
```

This keeps typography more consistent across desktop and mobile displays.

---

## Adaptive Backgrounds

Another challenge was displaying the illustrated background correctly on phones with very different aspect ratios.

The app uses:

```python
fit_mode="cover"
```

so the image always fills the screen without being stretched or distorted.

However, a single image can be cropped differently on very tall and narrow displays.

To improve this, the application calculates the screen aspect ratio:

```python
ratio = Window.width / Window.height
```

It then selects between two background assets:

```python
if ratio < 0.48:
    background_source = "images/background_tall.png"
else:
    background_source = "images/background.png"
```

This allows tall mobile displays to use an illustration composed specifically for that screen shape, while standard displays use the original version.

---

## Mobile Popup and Keyboard Handling

The food-management popup required additional work for Android.

On mobile devices, opening the software keyboard can cover a large part of the application window. Earlier versions could leave form controls hidden or difficult to reach.

The final popup uses one scrollable content area containing:

- the food list
- add-food input
- add button
- delete-food input
- delete button
- status messages

The application uses:

```python
Window.softinput_mode = "below_target"
```

on Android.

When an input receives focus, the popup also scrolls toward that widget:

```python
content_scroll.scroll_to(
    instance,
    padding=dp(16),
    animate=True,
)
```

This ensures that the form remains usable even when the Android keyboard occupies a large part of the screen.

---

## Project Evolution

### 1. Local Python prototype

The original version stored foods locally in a JSON file.

This first implementation focused on:

- Python fundamentals
- application logic
- random selection
- reading and writing data
- add and delete operations
- simple persistence

### 2. Kivy graphical interface

The project was then developed into a graphical Kivy application.

This introduced:

- widgets
- layouts
- buttons
- labels
- text inputs
- popups
- custom styling
- image assets
- custom fonts

### 3. Supabase persistence

The local JSON storage was replaced with a Supabase database.

This introduced remote persistence and REST API communication.

The application communicates with Supabase through `requests` rather than the full Supabase Python SDK.

This keeps the Android dependency tree significantly lighter.

### 4. Android packaging

The project was packaged for Android using Buildozer and python-for-android.

The Android configuration includes:

- portrait orientation
- Internet permission
- Android API 35
- minimum Android API 24
- custom application icon
- Python and Kivy dependencies

### 5. Android dependency debugging

An earlier implementation used the Supabase Python SDK.

During Android builds, some of its transitive dependencies required packages that were problematic to cross-compile for Android.

The Supabase integration was therefore simplified to direct REST requests using `requests`.

This reduced the dependency tree while preserving the database functionality required by the application.

### 6. Device testing and responsive redesign

After producing a working APK, the earlier version of the application was tested on physical Android devices.

This revealed differences that were not visible during desktop development, including:

- inconsistent physical widget sizes
- screen-density differences
- background cropping
- mobile keyboard behaviour
- popup positioning
- controls hidden behind the keyboard

The UI was progressively redesigned using `dp`, `sp`, responsive positioning, scrollable content, and adaptive image assets.

### 7. Authentication and database security

Supabase Authentication was added using direct REST requests.

This introduced:

- account registration
- email confirmation
- login
- logout
- access-token handling
- separate authentication screens
- protected database requests

Row Level Security was then enabled to prevent anonymous access to the `foods` table.

Automated tests were also added for the authentication and Supabase clients.

---

## Screenshots

### Main Screen

![Food App main screen](screenshots/home.png)

### Food List Management

![Food list management](screenshots/food-list.png)

---

## Technologies

### Application

- Python
- Kivy

### Backend and data

- Supabase
- Supabase Auth
- PostgreSQL
- Supabase REST API
- Row Level Security
- Requests

### Testing

- pytest
- pytest-cov
- unittest.mock

### Android

- Buildozer
- python-for-android
- Android SDK / NDK

### Development and deployment

- Git
- GitHub
- GitHub Actions
- GitHub Pages

---

## Project Structure

```text
food_kivy/
├── .github/
│   └── workflows/
│       └── build-apk.yml
├── docs/
│   └── index.html
├── fonts/
│   └── Pacifico-Regular.ttf
├── images/
│   ├── background.png
│   ├── background_tall.png
│   └── icon.png
├── screenshots/
│   ├── home.png
│   └── food-list.png
├── supabase/
│   └── migrations/
│       └── 20260909_enable_foods_rls.sql
├── tests/
│   ├── test_auth_client.py
│   └── test_supabase_client.py
├── .gitignore
├── auth_client.py
├── auth_screen.py
├── buildozer.spec
├── main.py
├── signup_screen.py
├── supabase_client.py
├── ui_components.py
└── README.md
```

A local `config.py` file is also required, but it is intentionally excluded from Git because it contains the Supabase project configuration.

---

## Configuration

Create a file named:

```text
config.py
```

in the project root.

Add:

```python
SUPABASE_URL = "your-supabase-project-url"
SUPABASE_KEY = "your-supabase-publishable-or-anon-key"
```

Use the Supabase publishable key or legacy `anon` key.

Never place the `service_role` key inside the application.

`config.py` is included in `.gitignore` and should not be committed with real project configuration.

---

## Run Locally

Clone the repository:

```bash
git clone https://github.com/laurabaraldi98-lgtm/food_kivy.git
```

Enter the project directory:

```bash
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

Install the dependencies:

```bash
pip install kivy requests pytest pytest-cov
```

Create the local `config.py` file with the required Supabase values.

Then run:

```bash
python main.py
```

---

## Tests

Run the automated tests with:

```bash
python -m pytest
```

Run the tests with coverage for the two HTTP client modules:

```bash
python -m pytest --cov=auth_client --cov=supabase_client --cov-report=term-missing
```

The current test suite contains nine tests covering:

- signup
- login
- logout
- authenticated headers
- retrieving foods
- adding foods
- deleting foods
- HTTP error handling

The current tests provide 100% statement coverage for `auth_client.py` and `supabase_client.py`.

This percentage does not represent coverage of the complete Kivy interface.

---

## Android Build

Android packaging is configured in `buildozer.spec`.

The application currently uses:

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
```

The custom application icon is configured with:

```ini
icon.filename = images/icon.png
```

Buildozer and python-for-android are used to produce the Android application package.

The repository also contains a GitHub Actions workflow for automated Android builds.

Earlier versions were successfully built and tested on physical Android devices. The current authentication version has been tested on desktop but still needs a new Android build and physical-device test.

---

## Current Limitations

The application is functional, but some important features are still under development.

Currently:

- all authenticated users share the same food list
- foods are not yet connected to an owner or group
- users cannot yet create private or shared group lists
- the session is stored only while the application is running
- users must log in again after restarting the application
- access-token refresh is not yet implemented
- database requests are synchronous
- the application requires an Internet connection
- network failures have limited user-facing error handling
- the interface is currently available only in Italian
- the current authentication version still needs to be tested on Android

---

## Planned User and Group Lists

The next development step is to make food lists belong to specific users and groups.

The planned database model will include:

- a `groups` table
- a `group_members` table
- a `group_id` column in the `foods` table

A personal list will be represented by a group containing one user. A shared list will use the same structure but contain multiple selected users.

New Row Level Security policies will allow users to access only foods belonging to groups of which they are members.

This work will be completed in a separate feature branch.

---

## Possible Future Improvements

Potential future versions could include:

- private food lists
- shared household or group lists
- group invitations
- group roles and permissions
- multiple lists
- food categories
- filters
- favourites
- persistent login
- automatic token refresh
- better network error feedback
- loading indicators
- asynchronous requests
- retry handling
- offline caching
- synchronization after reconnecting
- animations and additional UI polish
- additional languages
- automated Kivy interface tests

---

## What I Learned

This project gave me practical experience with more than the initial application logic.

### Python and application structure

- separating responsibilities between files
- object-oriented programming
- inheritance
- application state management
- writing reusable functions
- working with external configuration
- exception handling

### Kivy

- widgets and layouts
- screen management
- buttons and labels
- text inputs
- popups and dropdown menus
- canvas drawing
- custom UI components
- custom fonts
- responsive positioning
- `dp` and `sp`
- mobile keyboard behaviour

### Authentication and security

- account registration
- login and logout flows
- email confirmation
- access tokens
- authenticated HTTP requests
- Row Level Security
- PostgreSQL policies

### APIs and databases

- REST API requests
- HTTP methods
- HTTP headers
- JSON payloads
- remote persistence
- Supabase
- PostgreSQL
- SQL migrations

### Testing

- pytest
- mocking HTTP requests
- testing successful responses
- testing HTTP errors
- measuring code coverage

### Android development

- Buildozer configuration
- python-for-android
- Android SDK and NDK configuration
- dependency compatibility
- APK builds
- testing on physical devices
- debugging differences between desktop and Android

### Responsive design

- pixel density
- physical versus logical dimensions
- aspect ratios
- image cropping
- adaptive assets
- mobile-specific layout problems

### Git and CI

- feature branches
- commits
- merges
- GitHub Actions
- GitHub Pages
- iterative testing and debugging

---

## Status

The current version includes:

- account registration
- email confirmation
- login and logout
- authenticated Supabase requests
- Row Level Security
- remote food persistence
- random food selection
- add and delete operations
- responsive Kivy interface
- Android keyboard support
- adaptive backgrounds
- custom application branding
- nine automated client tests

The authentication flow and food operations are working correctly on desktop.

The next major development phase will introduce user-owned and group-shared food lists with membership-based database policies.
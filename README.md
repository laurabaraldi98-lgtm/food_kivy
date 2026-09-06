# Food App

A responsive food suggestion app built with Python and Kivy, available on desktop and Android.

The app solves a simple everyday problem: deciding what to eat.

Users can maintain a list of foods, add or remove items, and let the app randomly choose one. The list is stored remotely in Supabase, so changes persist between sessions and across devices using the same shared database.

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

What began as a small Python project gradually evolved into a cross-platform application involving remote persistence, REST API communication, Android packaging, responsive UI design, mobile keyboard handling, CI builds, and debugging across different physical devices.

---

## Features

- Random food suggestion
- Add new foods
- Remove existing foods
- Persistent food list stored in Supabase
- Supabase REST API integration
- Shared food list across sessions
- Responsive Kivy interface
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

---

## How It Works

When the application starts, it loads the current food list from a Supabase `foods` table.

The Supabase communication is isolated in `supabase_client.py` and uses standard HTTP requests.

The application performs three main operations:

- `GET` — retrieve the current food list
- `POST` — add a new food
- `DELETE` — remove an existing food

The REST endpoint is built from the Supabase project URL:

```python
BASE_URL = f"{SUPABASE_URL}/rest/v1/foods"
```

The app then sends requests using the Supabase API key through HTTP headers.

When a food is added or deleted, the database is updated immediately. This means the list is still available after closing and reopening the app.

At the moment, the application uses one shared food list rather than separate user accounts.

---

## User Interface

The main screen contains two primary actions:

### Choose for me

The app randomly selects one food from the current list and displays the result.

### View food list

Opens the food-management popup where users can:

- view all saved foods
- add a new food
- remove an existing food

The popup also displays status feedback when an item is added, already exists, is removed, or cannot be found.

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

This allows tall mobile displays to use an illustration composed specifically for that screen shape while standard displays use the original version.

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
    animate=True
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

The application now communicates with Supabase through `requests` rather than the full Supabase Python SDK.

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

After producing a working APK, the application was tested on physical Android devices.

This revealed differences that were not visible during desktop development, including:

- inconsistent physical widget sizes
- screen-density differences
- background cropping
- mobile keyboard behaviour
- popup positioning
- controls hidden behind the keyboard

The UI was progressively redesigned using `dp`, `sp`, responsive positioning, scrollable content, and adaptive image assets.

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

### Backend / Data

- Supabase
- PostgreSQL
- Supabase REST API
- Requests

### Android

- Buildozer
- python-for-android
- Android SDK / NDK

### Development

- Git
- GitHub
- GitHub Actions

---

## Project Structure

```text
food_kivy/
├── .github/
│   └── workflows/
│
├── fonts/
│   └── Pacifico-Regular.ttf
│
├── images/
│   ├── background.png
│   ├── background_tall.png
│   └── icon.png
│
├── screenshots/
│   ├── home.png
│   └── food-list.png
│
├── .gitignore
├── buildozer.spec
├── main.py
├── supabase_client.py
└── README.md
```

A local `config.py` file is also required, but it is intentionally excluded from Git because it contains Supabase configuration.

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
SUPABASE_KEY = "your-supabase-key"
```

`config.py` is included in `.gitignore` and should not be committed with real credentials.

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

```bash
.venv\Scripts\activate
```

Install the desktop dependencies:

```bash
pip install kivy requests
```

Create your local `config.py` with the required Supabase values.

Then run:

```bash
python main.py
```

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

The custom launcher icon is configured with:

```ini
icon.filename = images/icon.png
```

Buildozer and python-for-android are used to produce the Android application package.

The repository also contains a GitHub Actions workflow used for automated Android builds.

---

## Current Limitations

The project is functional, but there are still areas that could be expanded.

Currently:

- there is one shared food list
- there is no authentication
- users do not have separate private lists
- the application requires an Internet connection to access Supabase
- network failures have limited user-facing error handling
- the UI is currently only available in Italian

---

## Possible Future Improvements

Potential future versions could include:

- user authentication
- private food lists
- shared household or group lists
- multiple lists
- food categories
- filters
- favourites
- better network error feedback
- loading indicators
- retry handling
- offline caching
- synchronization after reconnecting
- animations and additional UI polish
- additional languages
- automated UI testing

---

## What I Learned

This project gave me practical experience with more than the initial application logic.

### Python and application structure

- separating responsibilities between files
- handling application state
- writing reusable functions
- working with external configuration

### Kivy

- layouts and widgets
- popups
- scroll views
- text inputs
- canvas drawing
- custom rounded buttons
- custom fonts
- responsive positioning
- `dp` and `sp`
- mobile keyboard behaviour

### APIs and databases

- REST API requests
- HTTP methods
- HTTP headers
- JSON payloads
- remote persistence
- Supabase
- PostgreSQL-backed data

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
- physical vs logical dimensions
- aspect ratios
- image cropping
- adaptive assets
- mobile-specific layout problems

### Git and CI

- feature branches
- commits
- merges
- resolving branch divergence
- GitHub Actions
- iterative testing and debugging

---

## Status

The core application is working on desktop and Android.

Current functionality includes:

- remote food persistence
- random food selection
- add and delete operations
- responsive mobile UI
- Android keyboard support
- adaptive backgrounds
- custom app branding

Further development will focus on user-specific data, stronger error handling, and additional product features.
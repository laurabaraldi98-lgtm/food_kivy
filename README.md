# Food App

A simple food suggestion application built with Python and Kivy.

The app helps users decide what to eat by randomly selecting a food from a customizable list. Users can add new foods, remove existing foods, and keep their list saved between sessions.

The application interface is currently in Italian.

## Features

* Random food suggestion
* Add new foods to the list
* Remove foods from the list
* Save the food list locally
* Preserve added and removed foods between sessions
* Simple graphical interface
* Italian-language interface
* Desktop support
* Android version in development

## How It Works

The application contains a customizable list of food options.

Users can:

1. Add a new food to the list.
2. Remove a food they no longer want.
3. Ask the app to randomly select one of the available foods.

The food list is stored locally in a JSON file. This means that changes remain saved even after the application is closed and reopened.

## Technologies Used

* Python
* Kivy
* JSON
* Buildozer
* Git
* GitHub

## Installation

### Run the App on Desktop

Make sure Python is installed on your computer.

Clone the repository:

```bash
git clone YOUR_REPOSITORY_LINK
```

Open the project folder:

```bash
cd YOUR_PROJECT_FOLDER
```

Install Kivy:

```bash
pip install kivy
```

Run the application:

```bash
python main.py
```

Replace `YOUR_REPOSITORY_LINK` with the link to this GitHub repository.

Replace `YOUR_PROJECT_FOLDER` with the real name of the project folder.

## Android Version

The Android version is built using Buildozer.

Buildozer normally needs to be used in a Linux environment, such as Ubuntu or Windows Subsystem for Linux.

Example build command:

```bash
buildozer android debug
```

After a successful build, the APK file should be available inside the `bin` folder.

The Android version is currently under development and still requires additional debugging and testing.

## Project Structure

```text
food-app/
│
├── main.py
├── buildozer.spec
├── foods.json
├── README.md
└── other project files
```

The exact file names may vary depending on the current version of the project.

## What I Learned

Through this project, I practiced:

* Creating a graphical interface with Kivy
* Handling button events
* Working with Python functions
* Working with lists and dictionaries
* Adding items dynamically
* Removing items dynamically
* Selecting random values
* Reading data from JSON files
* Writing data to JSON files
* Preserving data between sessions
* Organizing a Python project
* Using Git and GitHub
* Preparing a Python application for Android

## Language

The application interface is currently available in Italian.

An English version may be added in the future.

## Future Improvements

Possible future improvements include:

* English-language support
* Food categories
* Search and filtering options
* Improved visual design
* Custom food images
* Better error handling
* Improved Android compatibility

## Project Status

The desktop version is available for testing.

The Android version is currently being debugged.

## Author

Created by Laura Baraldi as a Python and Kivy learning project.

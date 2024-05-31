# tk-clarisse

`tk-clarisse` is a ShotGrid Toolkit engine for clarisse, providing seamless integration with ShotGrid. 

This engine allows artists and technical directors to access ShotGrid functionality directly within clarisse.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Environments](#environments)
- [Configuration](#configuration)
- [Contributing](#contributing)

## Introduction

`tk-clarisse` integrates ShotGrid with clarisse, enabling a streamlined workflow for visual effects and animation production. 

By using this toolkit, users can easily manage assets, publish work, and track project progress within the clarisse environment.

## Environments
`tk-clarisse` has been tested in this environment:
- CentOS 7
- Shotgrid Desktop App 1.8.0
- clarisse 5.0.11
  - clarisse 5.0.11 provides python2 and python3, this code was written for python3.


## Features

- Asset Management: Browse and load assets directly from ShotGrid.
- Publishing: Publish your work to ShotGrid with metadata and version control.
- Task Management: View and manage your ShotGrid tasks within clarisse.
- Customizable UI: Tailor the toolkit interface to fit your pipeline needs.

## Installation

#### You must be prepared for [Shotgrid](https://shotgrid.autodesk.com/)  and Advanced Project Settings in Shotgrid Desktop App to use `tk-clarisse`!

The official [ShotGrid Developer Help Center](https://help.autodesk.com/view/SGDEV/ENU/) and [Shotgrid Community](https://community.shotgridsoftware.com/) can be helpful.


## Configuration
To configure `tk-clarisse`, add variables to `clarisse.env`, edit the environment yml files located in the `config` directory.


After adding the `tk-clarisse` engine, you can add various apps to `tk-clarisse`.


#### 1. Locate where you installed Pipeline Configuration

#### 2. Add `IX_PYTHON3HOME`, `IX_PYTHON3PATH`, `LD_LIBRARY_PATH` to `clarisse.env` recognition of python3 in `tk-clarisse` within clarisse.

```sh
# ~/.isotropix/clarisse/5.0/clarisse.env

IX_PYTHON2HOME=/usr/local:/usr
IX_PYTHON2PATH=/your/python2/libs/path
IX_PYTHON3HOME=/usr/local:/usr
IX_PYTHON3PATH=/your/python3/libs/path
ILISE_SERVER=Your_IP:port
IX_SHELF_CONFIG_FILE=$IX_PYTHON_API_PATH/shelves/shelf.cfg
IX_SHELF_SCRIPT_PATH=
IX_SHELF_ICON_PATH=
IX_MENU_CONFIG_FILE=$IX_PYTHON_API_PATH/menus/init_menus.py
IX_MENU_SCRIPT_PATH=
IX_MENU_ICON_PATH=
IX_RESOLUTION_PRESET=
CLARISSE_STARTUP_SCRIPT=
# Add LD_LIBRARY_PATH if you need.

```

#### 2. Add engine descriptor section to `config/env/includes/engine_locations.yml`:

```yaml
engines.tk-clarisse.location:
  type: git
  name: tk-clarisse
  version: v0.0.1
  path: "github.com/junopark00/tk-clarisse.git"
```

#### 3. Then, create `config/env/includes/settings/tk-clarisse.yml`:

```yaml
includes:
#  - ../app_locations.yml
  - ../engine_locations.yml
#  - ./tk-multi-loader2.yml
#  - ./tk-multi-publish2.yml
  - ./tk-multi-workfiles2.yml

# asset_step
settings.tk-clarisse.asset_step:
apps:
   # tk-multi-about:
   #   location: "@apps.tk-multi-about.location"
   # tk-multi-loader2: "@settings.tk-multi-loader2.clarisse"
   # tk-multi-publish2: "@settings.tk-multi-publish2.clarisse.asset_step"
   tk-multi-workfiles2: "@settings.tk-multi-workfiles2.clarisse.asset_step"
menu_favourites:
  - {app_instance: tk-multi-workfiles2, name: File Open...}
  - {app_instance: tk-multi-workfiles2, name: File Save...}
#  - {app_instance: tk-multi-publish2, name: Publish...}
#  - {app_instance: tk-multi-loader2, name: Load}
location: '@engines.tk-clarisse.location'
```

#### 4. Update the apps using the `tank` command in your Pipeline Configurations folder:

```sh
./tank cache_apps
```

## Contributing
Welcome contributions to tk-clarisse.

To contribute:
1. Fork the repository.
2. Create a new branch (git checkout -b feature/your-feature-name).
3. Make your changes.
4. Commit your changes (git commit -m 'Add some feature').
5. Push to the branch (git push origin feature/your-feature-name).
6. Open a pull request.

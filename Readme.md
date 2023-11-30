# HuggingTui
HuggingTui is a VIM-inspired Huggingface Browser.

## Setup

### Using poetry

```sh
poetry install
```

### Using Nix & devenv

#### Development Environment

```sh
nix profile install nixpkgs#cachix
cachix use devenv
nix profile install --accept-flake-config tarball+https://install.devenv.sh/latest
devenv init
```

#### Activate Development Environment

```sh
devenv shell
```

## Usage
```sh
python3 htui.py
```

## TODO
- [ ] Support authentication/API keys
- [ ] Add a way to search for models
- [ ] Add a way to search for datasets


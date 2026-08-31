#!/bin/bash

set -e  # exit on error

# detect OS
OS=$(uname)

# function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

mkdir -p "$(dirname "$CONFIG_FILE")"

setup_ollama() {
        # update use_llm to true
        jq '.use_llm = true' "$CONFIG_FILE" > temp.json && mv temp.json "$CONFIG_FILE"
        # shellcheck disable=SC2162
        read -p "Do you want to start LLM automatically when Catnip launches? (y/n) " start_llm
        if [[ "$start_llm" =~ ^[Yy]$ ]]; then
            jq '.llm_on_start = true' "$CONFIG_FILE" > temp.json && mv temp.json "$CONFIG_FILE"
        else
            jq '.llm_on_start = false' "$CONFIG_FILE" > temp.json && mv temp.json "$CONFIG_FILE"
        fi

        # install Ollama and pull qwen3:8b model
        echo "Setting up Ollama for LLM support..."
        if [[ "$OS" == "Darwin" ]]; then
            if command_exists brew; then
                if ! command_exists ollama; then
                    echo "Installing Ollama via Homebrew..."
                    brew install ollama
                else
                    echo "Ollama is already installed."
                fi
            else
                echo "Homebrew is required to install Ollama. Please install Homebrew first: https://brew.sh/"
            fi
        elif [[ "$OS" == "Linux" ]]; then
            if ! command_exists ollama; then
                echo "Installing Ollama for Linux..."
                curl -fsSL https://ollama.com/install.sh | sh
            else
                echo "Ollama is already installed."
            fi
        elif [[ "$OS" == *"MINGW"* || "$OS" == *"MSYS"* || "$OS" == *"CYGWIN"* ]]; then
            echo "Please install Ollama manually for Windows: https://ollama.com/download"
        else
            echo "Unknown OS for Ollama installation. Please install Ollama manually."
        fi

        if command_exists ollama; then
            echo "Pulling qwen3:8b model for Ollama..."
            ollama pull qwen3:8b
            pkill -9 -f "Ollama" 2>/dev/null || true
        fi
}

setup_config() {
    CONFIG_DIR="$HOME/.config/catnip"
    CONFIG_FILE="$CONFIG_DIR/config.json"

    mkdir -p "$CONFIG_DIR"

    if [ ! -f "$CONFIG_FILE" ]; then
        cat <<EOF > "$CONFIG_FILE"
{
    "together_api_key": "",
    "use_llm": false,
    "llm_on_start": false,
    "app_theme": "nord",
    "editor_theme": "catnip"
}
EOF
        echo "Created default config at $CONFIG_FILE"
    else
        echo "Config file already exists at $CONFIG_FILE"
    fi
}

# function to install Python packages inside venv
install_python_packages() {
    echo "Setting up virtual environment..."

    if ! command_exists python3; then
        echo "Error: Python3 is not installed."
        if [[ "$OS" == "Darwin" ]]; then
            echo "Run: brew install python3"
        elif [[ "$OS" == "Linux" ]]; then
            echo "Run: sudo apt install python3 (Debian/Ubuntu) or sudo dnf install python3 (Fedora)"
        fi
        exit 1
    fi

    if ! command_exists pip3; then
        echo "Error: pip3 is not installed."
        echo "Run: python3 -m ensurepip --default-pip"
        exit 1
    fi

    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        sleep 2
    fi

    PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        source "$PROJECT_DIR/.venv/Scripts/activate"
    else
        source "$PROJECT_DIR/.venv/bin/activate"
    fi
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r "$PROJECT_DIR/requirements.txt"
}

# Install dependencies based on OS
install_mac() {
    if ! command_exists brew; then
        echo "Homebrew is required but not installed. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi

    if ! command_exists python3; then
        echo "Python is not installed. Installing via Homebrew..."
        brew install python3
    fi

    if ! command_exists pip3; then
        echo "pip is missing. Installing..."
        python3 -m ensurepip --default-pip
    fi

    if ! command_exists zenity; then
        echo "Zenity is not installed. Installing via Homebrew..."
        brew install zenity
    fi

    install_python_packages
}

install_linux() {
    if ! command_exists python3 || ! command_exists pip3; then
        echo "Python and pip are required but not found. Please install them first."
        exit 1
    fi

    if ! command_exists zenity; then
        echo "Installing Zenity..."
        if command_exists apt; then
            sudo apt update && sudo apt install -y zenity
        elif command_exists dnf; then
            sudo dnf install -y zenity
        elif command_exists yum; then
            sudo yum install -y zenity
        else
            echo "Unsupported Linux package manager. Please install Zenity manually."
            exit 1
        fi
    fi

    install_python_packages
}

install_windows() {
    if ! command_exists python; then
        echo "Python is not installed. Please install Python from https://www.python.org/downloads/"
        exit 1
    fi
    if ! command_exists pip; then
        echo "pip is missing. Please install Python with pip."
        exit 1
    fi

    python -c "import tkinter" 2>/dev/null || {
        echo "tkinter is missing. Please install Python with tkinter support."
        exit 1
    }

    install_python_packages
}

setup_symlink() {
    echo "Setting up global command 'catnip'..."
    SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
    SCRIPT_SOURCE="$SCRIPT_DIR/catnip"
    SCRIPT_TARGET="$HOME/.local/bin/catnip"

    if [ ! -f "$SCRIPT_SOURCE" ]; then
        echo "Error: catnip script not found at $SCRIPT_SOURCE"
        exit 1
    fi

    mkdir -p "$HOME/.local/bin"
    ln -sf "$SCRIPT_SOURCE" "$SCRIPT_TARGET"
    chmod +x "$SCRIPT_TARGET"

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
        echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> "$HOME/.zshrc"
        export PATH="$HOME/.local/bin:$PATH"
    fi

    if [ -L "$SCRIPT_TARGET" ]; then
        echo "Successfully created symlink at $SCRIPT_TARGET"
    else
        echo "Failed to create symlink"
        exit 1
    fi
}

if [[ "$1" == "--relink" ]]; then
    setup_symlink
    exit 0
elif [[ "$1" == "--llm" ]]; then
    setup_config
    setup_ollama
    exit 0
fi

# OS detection and installation
if [[ "$OS" == "Darwin" ]]; then
    install_mac
elif [[ "$OS" == "Linux" ]]; then
    install_linux
elif [[ "$OS" == *"MINGW"* || "$OS" == *"MSYS"* || "$OS" == *"CYGWIN"* ]]; then
    install_windows
else
    echo "Unsupported operating system: $OS"
    exit 1
fi

setup_symlink
setup_config

# shellcheck disable=SC2162
read -p "Do you want to enable LLM support? (y/n) " enable_llm
echo "Note: Enabling LLM support will use about 5GB of memory."

if [[ "$enable_llm" =~ ^[Yy]$ ]]; then
    setup_ollama
else
    echo "You can enable LLM support later by running ./install.sh --llm"
fi

echo "Installation complete! Run 'catnip' to start the app."
echo "The app may take a few seconds to start for the first time."
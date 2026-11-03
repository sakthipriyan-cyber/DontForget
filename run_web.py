"""Run the Don'tForget web application."""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from web.app import app

if __name__ == '__main__':
    print("Starting Don'tForget web application...")
    print("Open your browser to: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)

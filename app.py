#!/usr/bin/env python3
"""
Photobooth Flask Application - Main Entry Point
"""
import os
import logging
from flask import Flask
from photobooth import create_app

def main():
    """Main application entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/opt/photobooth/photobooth.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create Flask app
    app = create_app()
    
    # Get configuration
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logging.info(f"Starting Photobooth on {host}:{port}")
    
    # Run the application with Waitress in production
    if not debug:
        from waitress import serve
        serve(app, host=host, port=port, threads=4)
    else:
        app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
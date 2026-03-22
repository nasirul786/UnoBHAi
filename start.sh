#!/bin/bash
cd /www/wwwroot/bots/UnuRobot
source venv/bin/activate
exec python -m unu "$@"

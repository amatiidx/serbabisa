#!/bin/bash
(crontab -l 2>/dev/null; echo "0 9,13 * * 1-5 cd /home/ubuntu/serbabisa && /usr/bin/python3 master_precision_engine.py >> /home/ubuntu/serbabisa/engine.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "*/15 9-15 * * 1-5 cd /home/ubuntu/serbabisa && /usr/bin/python3 auto_scanner.py >> /home/ubuntu/serbabisa/auto.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 16 * * 1-5 cd /home/ubuntu/serbabisa && /usr/bin/python3 bandar_accumulation_scanner.py >> /home/ubuntu/serbabisa/bandar.log 2>&1") | crontab -

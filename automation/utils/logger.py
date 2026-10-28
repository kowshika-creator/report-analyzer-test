# -*- coding: utf-8 -*-
"""
AXON E2E Automation - Central Logging Utility
Outputs timestamped, structured logs to both console and disk.
"""

import os
import logging
from automation.config.settings import AutomationConfig

def get_logger(name: str = "AXON-E2E") -> logging.Logger:
    AutomationConfig.validate()
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler
        log_file_path = os.path.join(AutomationConfig.LOGS_DIR, "execution.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

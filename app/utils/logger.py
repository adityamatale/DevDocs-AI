import logging

# Configure logger
logger = logging.getLogger("ai_search_neon")
logger.setLevel(logging.INFO)

# Prevent logs from propagating to root logger
logger.propagate = False


if not logger.handlers:
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Terminal output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
import logging
import wrapt

handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt='{asctime} - {levelname} - {message}',
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{"
)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

LOGGER_ENABLED = True

def log(*, silence: bool = False):
    """Decorator to log function calls, their arguments and return values.

    Args:
        silence: If True, exceptions will be logged but not raised.
    """
    @wrapt.decorator(enabled=lambda: LOGGER_ENABLED)
    def inner(fn, instance, args, kwargs):
        try:
            result = fn(*args, **kwargs)
            logger.info(f"called with: {args=}, {kwargs=}")
            return result
        except Exception as ex:
            logger.error(f"called with: {args=}, {kwargs=}, ex={str(ex)}")
            if not silence:
                raise
    return inner

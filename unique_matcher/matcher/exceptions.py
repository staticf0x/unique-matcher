"""Errors for Unique Matcher."""


class BaseUMError(Exception):
    """Base error for all Unique Matcher errors."""


class CannotFindUniqueItemError(BaseUMError):
    """When no unique item can be found (e.g. the guides are missing)."""


class NotInFullHDError(BaseUMError):
    """When the processed screenshot is not in FullHD."""


class CannotFindItemBaseError(BaseUMError):
    """When parsing of item base fails."""


class CannotIdentifyUniqueItemError(BaseUMError):
    """When no item can be found in the screenshot."""


class InvalidTemplateDimensionsError(BaseUMError):
    """When, for whatever reason, the generated template is bigger than the cropped image."""

class BaseUMError(Exception):
    pass


class CannotFindUniqueItemError(BaseUMError):
    pass


class NotInFullHDError(BaseUMError):
    pass


class CannotFindItemBaseError(BaseUMError):
    pass


class CannotIdentifyUniqueItemError(BaseUMError):
    pass


class InvalidTemplateDimensionsError(BaseUMError):
    pass

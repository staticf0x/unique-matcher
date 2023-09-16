class BaseUMError(Exception):
    pass


class CannotFindUniqueItem(BaseUMError):
    pass


class NotInFullHD(BaseUMError):
    pass


class CannotFindItemBase(BaseUMError):
    pass


class CannotIdentifyUniqueItem(BaseUMError):
    pass


class InvalidTemplateDimensions(BaseUMError):
    pass

class BaseUMException(Exception):
    pass


class CannotFindUniqueItem(BaseUMException):
    pass


class NotInFullHD(BaseUMException):
    pass


class CannotFindItemBase(BaseUMException):
    pass


class CannotIdentifyUniqueItem(BaseUMException):
    pass


class InvalidTemplateDimensions(BaseUMException):
    pass

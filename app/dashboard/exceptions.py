class ServiceError(Exception):
    pass


class PasswordsMismatchError(ServiceError):
    pass


class UserAlreadyExistsError(ServiceError):
    pass


class NoAccessError(ServiceError):
    pass


class ProjectNotFoundError(ServiceError):
    pass


class UserNotOwnerError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class UnauthorizedError(ServiceError):
    pass


class UserNotFoundError(ServiceError):
    pass


class UserAlreadyHasAccessError(ServiceError):
    pass


class CannotInviteOwnerError(ServiceError):
    pass


class StorageError(ServiceError):
    pass


class UnsupportedFileTypeError(ServiceError):
    pass

class DocumentNotFoundError(ServiceError):
    pass

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

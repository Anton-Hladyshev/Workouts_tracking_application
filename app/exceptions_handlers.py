from fastapi import Request
from fastapi.responses import JSONResponse
from schemas.exceptions import BusinessRulesValidationError, InvalidPermissionsError, RegistrationError, TimeValidationError


def setup_exception_handlers(app):
    @app.exception_handler(TimeValidationError)
    async def time_validation_exception_handler(request: Request, exc: TimeValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.message
            }
        )

    @app.exception_handler(InvalidPermissionsError)
    async def permissions_validation_exception_handler(request: Request, exc: TimeValidationError):
        return JSONResponse(
            status_code=403,
            content={
                "detail": exc.message
            }
        )

    @app.exception_handler(BusinessRulesValidationError)
    async def business_logic_validation_exception_handler(request: Request, exc: BusinessRulesValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.message
            }
        )

    @app.exception_handler(RegistrationError)
    async def registration_exception_handler(request: Request, exc: RegistrationError):
        return JSONResponse(
            status_code=exc.code,
            content={
                "detail": exc.message
            }
        )
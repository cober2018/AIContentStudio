"""routers 包。"""

from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse


class CapabilityInputRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        protected = (
            "/creative-packages" in self.path or "/creative-executions" in self.path
            or "/channel-variants" in self.path or "/templates/channel-profiles/" in self.path
            or
            self.path.startswith(("/api/v1/provider-search", "/api/v1/provider-media/", "/api/v1/data-source-capabilities"))
            or self.path in {
                "/api/v1/materials/search", "/api/v1/materials/generate",
                "/api/v1/settings/renderer-probes", "/api/v1/settings/media-renderer-verifications",
                "/api/v1/settings/media-renderer-verifications/{verification_id}/revoke",
                "/api/v1/settings/publisher-verifications",
            }
            or self.path.endswith(("/asr-suggestions", "/media-render-previews", "/media-render-outputs", "/platform-binding", "/publisher-connection"))
        )

        async def safe_handler(request):
            try:
                return await handler(request)
            except RequestValidationError:
                # Default validation includes rejected values, which may contain credentials.
                if protected:
                    return JSONResponse(status_code=422, content={"detail": "capability_input_invalid"})
                raise

        return safe_handler

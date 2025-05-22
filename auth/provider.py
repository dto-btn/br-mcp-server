import msal
from mcp.server.auth.provider import OAuthAuthorizationServerProvider, AuthorizationParams, AuthorizationCode, RefreshToken, AccessToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from typing import Optional

class MSAuthProvider(OAuthAuthorizationServerProvider):
    """
    Microsoft Authorization Server Provider
    Implements the required OAuthAuthorizationServerProvider methods for Microsoft OAuth.
    """

    async def get_client(self, client_id: str) -> Optional[OAuthClientInformationFull]:
        """Retrieves client information by client ID."""
        # You may want to implement client lookup logic here
        return None

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Saves client information as part of registering it."""
        # Registration is typically handled in Azure Portal for MSAL
        pass

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        """Handles the /authorize endpoint and returns a redirect URL for Microsoft OAuth."""
        # Build the authorization URL for Microsoft login
        flow = self.app.initiate_auth_code_flow(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        return flow["auth_uri"]

    async def load_authorization_code(self, client: OAuthClientInformationFull, authorization_code: str) -> Optional[AuthorizationCode]:
        """Loads an AuthorizationCode by its code."""
        # Not typically needed with MSAL, handled in exchange_authorization_code
        return None

    async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
        """Exchanges an authorization code for an access token and refresh token."""
        # Exchange the authorization code for tokens
        result = self.app.acquire_token_by_authorization_code(
            code=authorization_code.code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        if "access_token" in result:
            return OAuthToken(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                id_token=result.get("id_token"),
                expires_in=result.get("expires_in")
            )
        else:
            raise Exception(result.get("error_description", "Unknown error during token exchange"))

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> Optional[RefreshToken]:
        """Loads a RefreshToken by its token string."""
        # Not typically needed with MSAL, handled in exchange_refresh_token
        return None

    async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        """Exchanges a refresh token for an access token and refresh token."""
        # Use the refresh token to get a new access token
        result = self.app.acquire_token_by_refresh_token(
            refresh_token.token,
            scopes or self.scopes
        )
        if "access_token" in result:
            return OAuthToken(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                id_token=result.get("id_token"),
                expires_in=result.get("expires_in")
            )
        else:
            raise Exception(result.get("error_description", "Unknown error during refresh token exchange"))

    async def load_access_token(self, token: str) -> Optional[AccessToken]:
        """Loads an access token by its token."""
        # MSAL does not provide a direct way to introspect tokens; you may need to decode JWT or validate externally
        return None

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        """Revokes an access or refresh token."""
        # MSAL does not provide a direct revoke method; you may need to call the Microsoft Graph API or rely on token expiry
        pass
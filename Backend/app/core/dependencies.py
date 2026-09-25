from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client, ClientOptions
from app.core.config import settings

security = HTTPBearer()

def get_supabase_client(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Client:
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    
    # Create a client that forwards the user's JWT
    # This ensures that RLS and Storage policies are naturally enforced by Supabase
    options = ClientOptions(
        headers={"Authorization": f"Bearer {token}"}
    )
    client: Client = create_client(
        settings.VITE_SUPABASE_URL, 
        settings.VITE_SUPABASE_ANON_KEY,
        options=options
    )
    
    # Verify the token is valid by getting the user
    try:
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        # Store user info inside client object for convenience in the endpoint
        client.auth_user = user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

    return client

import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL,
  realm: import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
});

export const initKeycloak = (onAuthenticated: () => void) => {
  keycloak
    .init({
      onLoad: 'check-sso',   
      checkLoginIframe: false,    
      pkceMethod: 'S256',
      redirectUri: window.location.origin + '/',
    })
    .then((authenticated) => {
      if (authenticated) {
        onAuthenticated();
      } else {
        keycloak.login({
          redirectUri: window.location.origin + '/',
        });
      }
    })
    .catch((error) => {
      console.error('Keycloak init failed:', error);
      // Don't auto-retry on error to prevent infinite loop
    });
};

export const doLogin = keycloak.login;
export const doLogout = keycloak.logout;
export const getToken = () => keycloak.token;
export const isLoggedIn = () => !!keycloak.token;
export const updateToken = (cb: () => void) =>
  keycloak.updateToken(5).then(cb).catch(doLogin);

export default keycloak;

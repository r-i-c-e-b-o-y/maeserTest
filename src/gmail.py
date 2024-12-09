import os
import ssl
from typing import Union
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError
from maeser.user_manager import User, BaseAuthenticator, LoginStyle


class EmailAuthenticator(BaseAuthenticator):
    def __init__(self, 
                 ldap_server_url: str, 
                 ldap_base_dn: str, 
                 ca_cert_path: str = '/etc/ssl/certs', 
                 connection_timeout: int = 5):
        self.ldap_server_url = ldap_server_url
        self.ldap_base_dn = ldap_base_dn
        self.ca_cert_path = ca_cert_path
        self.connection_timeout = connection_timeout

        # Ensure certificate directory exists
        if not os.path.exists(self.ca_cert_path):
            raise FileNotFoundError('Path to CA Certificates directory does not exist')

        # Initialize LDAP server instance
        self.ldap_server = self._initialize_ldap_server()
        
        # Login style
        self._login_style = LoginStyle('envelope-fill', 'maeser.login', direct_submit=False)

    def __str__(self):
        return "Email"

    @property
    def style(self):
        return self._login_style

    def _initialize_ldap_server(self) -> Server:
        """
        Initialize LDAP server instance with retrieved certificates.

        Returns:
            Server: An initialized LDAP Server object.
        """
        try:
            return Server(
                self.ldap_server_url,
                use_ssl=True,
                get_info=ALL,
                connect_timeout=self.connection_timeout,
                tls=Tls(validate=ssl.CERT_REQUIRED, ca_certs_path=self.ca_cert_path)
            )
        except LDAPException as e:
            print(f'Unable to initialize LDAP server {self.ldap_server_url}: {type(e)}, {e}')
            return None

    def authenticate(self, email: str, password: str) -> Union[tuple, None]:
        try:
            conn = Connection(
                self.ldap_server,
                user=f'mail={email},{self.ldap_base_dn}',
                password=password,
                auto_bind=True,
                read_only=True,
                receive_timeout=self.connection_timeout
            )
        except (LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError) as e:
            print(f'Email user {email} failed to authenticate: {type(e)}: {e}')
            return None

        try:
            conn.search(
                self.ldap_base_dn,
                f'(mail={email})',
                SUBTREE,
                attributes=['mail', 'displayName', 'memberOf'],
                time_limit=int(self.connection_timeout)
            )
            if conn.entries:
                display_name = conn.entries[0].displayName
                user_group = conn.entries[0].memberOf
                return email, display_name, user_group
        except LDAPSocketReceiveError as e:
            print(f'LDAP search timed out for user {email}: {e}')
        finally:
            conn.unbind()
        
        return None

    def fetch_user(self, email: str) -> Union[User, None]:
        """
        Fetch user information from LDAP and return a User object.
        This method performs an anonymous bind and searches for the user.
        No authentication is performed using this method.

        Args:
            email (str): The user's email.

        Returns:
            Union[User, None]: The User object if found, None otherwise.
        """
        try:
            conn = Connection(self.ldap_server, auto_bind=True, receive_timeout=self.connection_timeout)
        except (LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError) as e:
            print(f'LDAP fetch for user {email} failed: {type(e)}, {e}')
            return None
        
        try:
            search_filter = f'(mail={email})'
            conn.search(
                self.ldap_base_dn, 
                search_filter, 
                SUBTREE, 
                attributes=['mail', 'displayName', 'memberOf'],
                time_limit=int(self.connection_timeout)
            )
            
            if conn.entries:
                display_name = conn.entries[0].displayName.value
                user_group = conn.entries[0].memberOf.value
                return User(email, realname=display_name, usergroup=user_group, authmethod='email')
        except LDAPSocketReceiveError as e:
            print(f'LDAP search timed out for user {email}: {e}')
        finally:
            conn.unbind()

        print(f'No email user "{email}" found')
        return None
import os
import ssl
from typing import Union
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError
from maeser.user_manager import User, BaseAuthenticator, LoginStyle

class CAEDMAuthenticator(BaseAuthenticator):
    def __init__(self, ca_cert_path: str = '/etc/ssl/certs', connection_timeout: int = 5):
        self.ca_cert_path = ca_cert_path
        self.connection_timeout = connection_timeout

        # LDAP Server Configuration
        self.ldap_addresses = [
            'ctldap.et.byu.edu',
            'cbldap.et.byu.edu'
        ]
        self.ldap_base_dn = 'ou=accounts,ou=caedm,dc=et,dc=byu,dc=edu'

        # Ensure certificate directory exists
        if not os.path.exists(self.ca_cert_path):
            raise FileNotFoundError('Path to CA Certificates directory does not exist')

        # Initialize LDAP server instances
        self.ldap_server_instances = self._initialize_ldap_servers()
        self.ldap_usable_servers = self._test_ldap_anonymous_bind()
        self._next_server_index = 0
        self._login_style = LoginStyle('c-square-fill', 'maeser.login', direct_submit=False)
        
    def __str__(self):
        return "CAEDM"
    
    @property
    def style(self):
        return self._login_style

    @property
    def next_ldap_server(self)-> Union[Server, None]:
        """Return the next available LDAP server in a round-robin fashion."""
        if len(self.ldap_usable_servers) == 0:
            print("NO REACHABLE LDAP SERVER!")
            return None
        server_to_use = self.ldap_usable_servers[self._next_server_index]
        self._next_server_index = (self._next_server_index + 1) % len(self.ldap_usable_servers)
        return server_to_use

    def _initialize_ldap_servers(self) -> list[Server]:
        """
        Initialize LDAP server instances with retrieved certificates.

        Returns:
            list: A list of initialized LDAP Server objects.
        """
        servers: list[Server] = []
        for server_url in self.ldap_addresses:
            try:
                servers.append(Server(
                    server_url,
                    use_ssl=True,
                    get_info=ALL,
                    connect_timeout=self.connection_timeout,
                    tls=Tls(validate=ssl.CERT_REQUIRED, ca_certs_path=self.ca_cert_path)
                ))
            except LDAPException as e:
                print(f'Unable to initialize LDAP server {server_url}: {type(e)}, {e}')
        return servers

    def _test_ldap_anonymous_bind(self) -> list:
        """
        Test anonymous bind to each LDAP server and blacklist bad servers.

        Returns:
            list: A list of LDAP servers that are usable.
        """
        usable_servers = []
        for ldap_server in self.ldap_server_instances:
            try:
                test_connection = Connection(ldap_server, receive_timeout=self.connection_timeout)
                if test_connection.bind():
                    usable_servers.append(ldap_server)
                test_connection.unbind()
            except (LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError) as e:
                print(f'Failed to bind to LDAP server {ldap_server}: {type(e)}, {e}')
        return usable_servers

    def authenticate(self, ident: str, password: str) -> Union[tuple, None]:
        if self.next_ldap_server is None:
            return None
        try:
            conn = Connection(
                self.next_ldap_server,
                user=f'cn={ident},{self.ldap_base_dn}',
                password=password,
                auto_bind=True,
                read_only=True,
                receive_timeout=self.connection_timeout
            )
        except (LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError) as e:
            print(f'CAEDM user {ident} failed to authenticate: {type(e)}: {e}')
            return None

        try:
            conn.search(
                self.ldap_base_dn,
                f'(cn={ident})',
                SUBTREE,
                attributes=['cn', 'displayName', 'CAEDMUserType'],
                time_limit=int(self.connection_timeout)
            )
            if conn.entries:
                display_name = conn.entries[0].displayName
                user_group = conn.entries[0].CAEDMUserType
                return ident, display_name, user_group
        except LDAPSocketReceiveError as e:
            print(f'LDAP search timed out for user {ident}: {e}')
        finally:
            conn.unbind()
        
        return None

    def fetch_user(self, ident: str) -> Union[User, None]:
        """
        Fetch user information from LDAP and return a User object.
        This method performs an anonymous bind and searches for the user.
        No authentication is preformed using this method.

        Args:
            ident (str): The user's identifier.

        Returns:
            Union[User, None]: The User object if found, None otherwise.
        """
        if self.next_ldap_server is None:
            return None
        try:
            conn = Connection(self.next_ldap_server, auto_bind=True, receive_timeout=self.connection_timeout)
        except (LDAPException, LDAPAttributeError, LDAPBindError, LDAPSocketReceiveError) as e:
            print(f'LDAP fetch for user {ident} failed: {type(e)}, {e}')
            return None
        
        try:
            search_filter = f'(cn={ident})'
            search_base = 'ou=accounts,ou=caedm,dc=et,dc=byu,dc=edu'
            conn.search(
                search_base, 
                search_filter, 
                SUBTREE, 
                attributes=['cn', 'displayName', 'CAEDMUserType'],
                time_limit=int(self.connection_timeout)
            )
            
            if conn.entries:
                display_name = conn.entries[0].displayName.value
                user_group = conn.entries[0].CAEDMUserType.value
                return User(ident, realname=display_name, usergroup=user_group, authmethod='caedm')
        except LDAPSocketReceiveError as e:
            print(f'LDAP search timed out for user {ident}: {e}')
        finally:
            conn.unbind()

        print(f'No CAEDM user "{ident}" found')
        return None

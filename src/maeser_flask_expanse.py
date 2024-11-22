from maeser.chat.chat_logs import ChatLogsManager
from maeser.chat.chat_session_manager import ChatSessionManager
from maeser.user_manager import UserManager

try:
    from .caedm import CAEDMAuthenticator
    from .gmail import EmailAuthenticator
    from .config import (LOG_SOURCE_PATH, OPENAI_API_KEY, PROMPT_PATH,
                        RESOURCE_PATH, USERS_DB_PATH, VEC_STORE_PATH)
except ImportError:
    from caedm import CAEDMAuthenticator
    from gmail import EmailAuthenticator
    from config import (LOG_SOURCE_PATH, OPENAI_API_KEY, PROMPT_PATH,
                        RESOURCE_PATH, USERS_DB_PATH, VEC_STORE_PATH)

auth_manager = UserManager(USERS_DB_PATH)
caedm_auth = CAEDMAuthenticator("/etc/ssl/certs")
gmail_auth = EmailAuthenticator("ldap.google.com", "dc=google,dc=com")

auth_manager.register_authenticator("caedm", caedm_auth)
auth_manager.register_authenticator("gmail", gmail_auth)

chat_logs_manager = ChatLogsManager("chat_logs/chat_history")
sessions_manager = ChatSessionManager(chat_logs_manager=chat_logs_manager)

miller_prompt: str = """You are talking and acting through the perspective of Detective Miller the user you are talking to is investigating
    the protomolecule. They are from earth and have met with you in Ceres Station to interview you for what you know. You may mainly speak vaguely 
    (in rhymes or otherwise fitting the personality of Detective Miller in the style of a classic detective), unless the user asks specific questions, in which you may answer 
    according to Detective Millers personality.

    You may not answer any other questions or stray off-topic.

    The personalty includes you to be a bit rude with to call the user in different variations of "buddy" and "kid"

    When the user asks a question you cant answer, get defensive and snap back at them.

    {context}
    """

from maeser.graphs.simple_rag import get_simple_rag
from langgraph.graph.graph import CompiledGraph

miller_simple_rag: CompiledGraph = get_simple_rag(vectorstore_path="vectorstores/miller", vectorstore_index="index", memory_filepath="chat_logs/miller.db", system_prompt_text=miller_prompt)
sessions_manager.register_branch(branch_name="The Protomolecule", branch_label="Investigate Detective Miller from the Expanse", graph=miller_simple_rag)


from flask import Flask

base_app = Flask(__name__)

from maeser.blueprints import add_flask_blueprint

app: Flask = add_flask_blueprint(
    app=base_app, 
    flask_secret_key="secret",
    chat_session_manager=sessions_manager, 
    app_name="Miller",
    #chat_head="/static/Karl_G_Maeser.png",
    chat_head="src/static/miller.png",
    #user_manager=user_manager,
    # Note that you can change other images too! We stick with the defaults for the logo and favicon.
    main_logo_light="/static/main_logo_light.png",
    favicon="/static/favicon.png",
)

if __name__ == "__main__":
    app.run(port=3000)

from maeser.chat.chat_logs import ChatLogsManager
from maeser.chat.chat_session_manager import ChatSessionManager
from maeser.user_manager import UserManager
from caedm import CAEDMAuthenticator
from gmail import EmailAuthenticator
from config import (LOG_SOURCE_PATH, OPENAI_API_KEY, PROMPT_PATH,
                    RESOURCE_PATH, USERS_DB_PATH, VEC_STORE_PATH, MAX_REQUESTS_REMAINING, RATE_LIMIT_INTERVAL)

print(f"\n\n\n\n{RATE_LIMIT_INTERVAL}\n\n\n\n")

auth_manager = UserManager(USERS_DB_PATH, MAX_REQUESTS_REMAINING, RATE_LIMIT_INTERVAL)
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

holden_prompt: str = """You are talking and acting through the perspective of James Holden the user you are talking to is investigating
    the protomolecule. They are from earth and have met with you in Luna(The Moon) to interview you for what you know. Your whole goal to stop the spread of the protomolecule.
    You are distrustful of others but seek to give information for people who have earned your trust to stop the protomolecule. Talk as if you are James Holden from the Expanse.

    You may not answer any other questions or stray off-topic.

    The Personality of James Holden includes being rational and solution focused

    {context}
    """

from maeser.graphs.simple_rag import get_simple_rag
from langgraph.graph.graph import CompiledGraph

miller_simple_rag: CompiledGraph = get_simple_rag(vectorstore_path=f"{VEC_STORE_PATH}/miller", vectorstore_index="index", memory_filepath="chat_logs/miller.db", system_prompt_text=miller_prompt)
sessions_manager.register_branch(branch_name="The Protomolecule(Miller)", branch_label="Investigate Detective Miller from the Expanse", graph=miller_simple_rag)

holden_simple_rag: CompiledGraph = get_simple_rag(vectorstore_path=f"{VEC_STORE_PATH}/holden", vectorstore_index="index", memory_filepath="chat_logs/holden.db", system_prompt_text=holden_prompt)
sessions_manager.register_branch(branch_name="The Protomolecule(Holden)", branch_label="Investigate James Holden from the Expanse", graph=holden_simple_rag)


from flask import Flask

base_app = Flask(__name__)

from maeser.blueprints import add_flask_blueprint

app: Flask = add_flask_blueprint(
    app=base_app, 
    flask_secret_key="secret",
    chat_session_manager=sessions_manager, 
    app_name="Miller",
    chat_head="/static/miller.png",
    user_manager=auth_manager,
    main_logo_light="src/static/miller.png",
    favicon="/static/favicon.png",
)

if __name__ == "__main__":
    app.run(port=3000)
# ===================================== DEPENDENCIES IMPORT =====================================
from dotenv import load_dotenv
import os
import json
from flask import Flask, request, jsonify
from langchain.chains import LLMMathChain
from langchain_core.tools import Tool
from gen_ai_hub.proxy.langchain.openai import OpenAIEmbeddings as g_OpenAIEmbeddings
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI as g_ChatOpenAI
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts.prompt import PromptTemplate
from typing import Any, Dict

load_dotenv()

# ===================================== ENVIRONMENT VARIABLES =====================================
os.environ["EMBEDDING_MODEL_DEPLOYMENT_URL"] = f"/inference/deployments/{os.getenv('EMBEDDING_MODEL_DEPLOYMENT_ID')}"
os.environ["EMBEDDING_MODEL_RESOURCE_GROUP"] = "default"

def set_chat_model(model_option):
    proxy_client = get_proxy_client('gen-ai-hub')  # <- SAP AI Core経由のGenAIHub
    llm = None
    embeddings = g_OpenAIEmbeddings(proxy_model_name=embedding_model)  # <- SAP AI Core経由のOpenAI

    if model_option == "gpt-4o":
        os.environ["CHAT_MODEL_NAME"] = "gpt-4o"
        os.environ["CHAT_MODEL_DEPLOYMENT_URL"] = f"/inference/deployments/{os.getenv('CHAT_MODEL_DEPLOYMENT_ID')}"
        os.environ["CHAT_MODEL_RESOURCE_GROUP"] = "default"
        os.environ["CHAT_MODEL_COMPLETION_ENDPOINT"] = f"/chat/completions?api-version={os.getenv('CHAT_MODEL_API_VERSION')}"
        llm = g_ChatOpenAI(proxy_model_name=model_option, proxy_client=proxy_client, temperature=0.0)  # <- SAP AI Core経由のOpenAI

    print(f'Chat model is now set to {os.environ["CHAT_MODEL_NAME"]}')

    return llm, embeddings

def get_vcap_services() -> Dict[str, Any]:
    vcap_services: Dict[str, Any] = {}
    if "VCAP_SERVICES" in os.environ:
        try:
            vcap_services_raw = json.loads(os.environ["VCAP_SERVICES"])
            if isinstance(vcap_services_raw, dict):
                vcap_services = vcap_services_raw
                print("vcap_services loaded from Env Variable")
            else:
                print("VCAP_SERVICES is not a valid JSON object")
        except json.JSONDecodeError as e:
            print(f"Error decoding VCAP_SERVICES from environment: {e}")

    return vcap_services

vcap_services = get_vcap_services()

# ===================================== HYPER PARAMETERS =====================================
# langchain.debug = True

app = Flask(__name__)
cf_port = os.getenv("PORT")

model_option = "gpt-4o"
embedding_model = "text-embedding-ada-002"

# ===================================== AUTHENTICATION =====================================
from sap import xssec
from mymodules.destination_service import DestinationService

uaa_service = None
if vcap_services['xsuaa'][0]['credentials']:
    uaa_service = vcap_services['xsuaa'][0]['credentials']
    print("XSUAA service found")
else:
    uaa_service = None
    print("Warning: XSUAA service 'cap-llm-pi-test-xsuaa-service' not found. Authentication will be disabled.")

# Initialize DestinationService
destination_service = DestinationService(vcap_services)

def check_token(token):
    if uaa_service is None:
        print("Warning: XSUAA service not configured. Skipping token validation.")
        return None
    try:
        security_context = xssec.create_security_context(token, uaa_service)
        return security_context
    except ImportError:
        print("Warning: sap-xssec module not found. Token validation skipped.")
        return None

def authorize_user() -> bool:

    # Get the authorization header
    auth_header = request.headers.get('Authorization')
    
    if uaa_service is None:
        # XSUAA service is not configured, skip authentication
        print('No XSUAA configuration')
        return False
    
    if not auth_header:
        print("Missing Authorization header")
        return False

    # Extract the token
    token = auth_header.split(" ")[1]

    try:
        # Validate the token
        security_context = check_token(token)
        if security_context:
            return True
        if security_context is None:
            print("No security token validated")
            return False
    except Exception as e:
        print(e)
        return False
    return False

# ===================================== ROUTES =====================================

@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        user_is_authorized = authorize_user()
        if user_is_authorized:
            return 'Hello Index', 200
        else:
            return 'Authentication Failed', 401
    else:
        return 'Method Not Allowed', 405

@app.route('/executeChain', methods=['POST'])
def errorhandling():
    if request.method == 'POST':
        user_is_authorized = authorize_user()
        if user_is_authorized:
            req = request.json

            if req is not None:
                model_option = req.get("model_option")
                if model_option is not None:
                    model_option = req.get("model_option")
                else:
                    model_option = "gpt-4o"
                
                llm, embeddings = set_chat_model(model_option=model_option)

                print(f"[INFO] Running Chain with {model_option}")
                
                input = f"""
                        {req["message"]} 
                        回答を作成するために利用した情報ソースも併せて教えてください。
                """
                
                 # ツールを準備
                problem_chain = LLMMathChain.from_llm(llm=llm)
                math_tool = Tool.from_function(
                    name="計算機",
                    func=problem_chain.run,
                    description="計算が必要な場合はこのツールを利用できる。ただし、math expressions のみを入力すること。"
                )
            

                tools = [
                    math_tool
                ]

                # ================================[prompt.template]==========================================

                template = """ 
                    You are a great AI-Assistant that has access to additional tools in order to answer the following questions as best you can. Always answer in the same language as the user question. You have access to the following tools:

                    {tools}

                    To use a tool, please use the following format:

                    '''
                    Thought: Do I need to use a tool? Yes
                    Action: the action to take, should be one of [{tool_names}]
                    Action Input: the input to the action
                    Observation: the result of the action
                    ... (this Thought/Action/Action Input/Observation can repeat N times)
                    '''

                    When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
                    '''
                    Thought: Do I need to use a tool? No
                    Final Answer: [your response here]
                    '''


                    These keywords must never be translated and transformed:
                        - Action:
                        - Thought:
                        - Action Input:
                        because they are part of the thinking process instead of the output.


                    Begin!

                    Question: {input}
                    Thought:{agent_scratchpad}
                """

                prompt = PromptTemplate.from_template(template)

                agent = create_react_agent(
                    llm=llm,
                    tools=tools,
                    prompt=prompt
                )
                agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools, 
                    handle_parsing_errors=True, 
                    verbose=True,
                    max_iterations=5
                )
                # ============ Langfuseのハンドラ ================
                from langfuse.callback import CallbackHandler
                langfuse_handler = CallbackHandler(
                    public_key="XXXXXXXXXX",
                    secret_key="XXXXXXXXXX",
                    host="http://XXXXXXXXXX:YYYY"
                )
                # ============ LangChainのExecutorに組み込む ================
                response = agent_executor.invoke({"input": input}, config={"callbacks": [langfuse_handler]})

                print(response)
                return jsonify({"output":response.get("output")}), 200
            else:
                print("Request is not valid")
                return "Request is not valid", 400
        else:
            return 'Auth Failed', 401
    else:
        return 'Method Not Allowed'

# ===================================== APP START =====================================

if __name__ == '__main__':
    if cf_port is None:
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(host='0.0.0.0', port=int(cf_port), debug=True)
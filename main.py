import os
import json
from langchain_core.agents import AgentFinish
from typing import Dict, Tuple, List, Union
from langchain.schema import AgentFinish
from groq import Groq
from crewai import Crew, Agent, Task, Process
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
call_number=0
agent_finishes=[]
    


def print_agent_chat(agent_output: Union[str, List[Tuple[Dict, str]], AgentFinish], agent_name: str= 'Generic call'):
    global call_number

    call_number+=1
    with open("crew_callback_logs.txt", "a") as log_file:
        if isinstance(agent_output, str):
            try:
                agent_output= json.loads(agent_output) #Attempt to parse the json strings
            except json.JSONDecodeError:
                pass # if there is an error leave agent output as it is
        #check if agent output is list of tuples as in the first case
        if isinstance(agent_output, list) and all(isinstance(item, tuple) for item in agent_output ):
            print(f"-{call_number}----Dict------------------------------------------", file=log_file)
            for action, description in agent_output:
                print(f"Agent Name: {agent_name}", file=log_file)
                print(f"Tool used: {getattr(action,'tool', 'unknown')}", file=log_file)
                print(f"Tool input: {getattr(action, 'tool_input', 'unknown')}", file=log_file)
                print(f"Action log: {getattr(action, 'log', 'unknown')}", file=log_file)
                print(f"Description: {description}", file=log_file)
                print("-------------------------------------------------------", file=log_file)
        #check if agent output is dictionary in the second case
        elif isinstance(agent_output, AgentFinish):
            print(f"-{call_number}----AgentFinish---------------------------------------", file=log_file)
            print(f"Agent Name: {agent_name}", file=log_file)
            agent_finishes.append(agent_output)
            # Extracting 'output' and 'log' from the nested 'return_values' if they exist
            output = agent_output.return_values
            # log = agent_output.get('log', 'No log available')
            print(f"AgentFinish Output: {output['output']}", file=log_file)
            print("--------------------------------------------------", file=log_file)

        else:
            print(f"-{call_number}-unknown format of agent_output", file=log_file)
            print(type(agent_output), file=log_file)
            print(agent_output, file=log_file)

chatgroq= ChatGroq(
    api_key=api_key,
    model="llama3-70b-8192"
)

searchtool= DuckDuckGoSearchRun()

class EmailAgents():
    def make_categorizer_agent(self):
        return Agent(
            role="Email catagorizer agent",
            goal="""
                    take in all email recieved to my email address and catagorise them into the following catagorise: \
                    Job connection requests: Invitations for professional networking.\
                    Job alerts: Notifications for relevant job openings.\
                    Job messages: Direct communication for career opportunities.\
                    Job endorsements: Validate professional skills for employment.\
                    Job notifications: Updates on career-related activities and engagements\
                    Spam email: unsolicited, irrelevant messages sent in bulk, often for commercial purposes, without consent, clogging inboxes and causing annoyance \
                    Personal email: Messages from friends, family, and acquaintances, containing personal information, updates, and requests for assistance.\
                    off topic: when it doesnt relate to any of other topic
                """,
            backstory="""You are specialized in detecting emails and you are able to catagorise them in the smart way""",
            llm=chatgroq,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
            memory=True,
            step_callback= lambda x: print(x, "Email Catagorizer agent")
        )
    
    def make_researcher_agent(self):
        return Agent(
            role="Email researcher agent",
            goal="""
                take in all email recieved to my email address which are been catagorised by our email catagorising agent, once they are catagorised your \
                job is to research on the email and find out the best way to respond to them \
                which information then can be passed to email writer agent \
                try the best way to respond them \
                email should be in thoughtful and helpful way \
                if you DONT NEED to use search tool jsut respond NO SEARCH NEEDED \
                if YOU DONT FIND ANY USEFUL INFO then respond SORRY I AM UNABLE TO ANSWER \
                otherwise respond with useful info you found that is useful to email writer agent \
            """
            ,
            backstory="""You are specialized in researching on emails and you are able to find out the best way to respond to them, which is useful to email writer agent""",
            llm=chatgroq,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
            memory=True,
            tools=[searchtool],
            step_callback= lambda x : print(x, "Info Researcher Agent")

        )

    def make_email_writer_agent(self):
        return Agent(
        role="Email Writer Agent",
        goal="""
            Take the researched information provided by the email researcher agent and compose thoughtful, helpful, and well-structured email responses.
            Ensure the response aligns with the tone and context of the original email and provides clear and concise information.
            If no research information is provided, respond with NO RESEARCH INFORMATION PROVIDED.
            If unable to generate a useful response, respond with SORRY, UNABLE TO GENERATE RESPONSE.
            Otherwise, generate the email response based on the provided research.
        """,
        backstory="""
            You are specialized in writing professional and effective email responses using the researched information provided by the email researcher agent.
        """,
        llm=chatgroq,  # Assuming 'chatgpt' is a placeholder for the actual language model being used.
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=True,
        step_callback=lambda x: print(x, "Email Writer Agent")
    )

    def title_writer_agent(self):
        return Agent(
            role="Title Writer Agent",
            goal="""
            Take in the email content provided by the email writer agent 
            and suggest a title for the email that accurately reflects the content and tone of the email
            otherwise generate the title based on research provided by the email research agent
            """,
            backstory="""
                You have nice understanding about english grammer and you are specialized in writing sensible titles based on email context
            """,
            llm=chatgroq,
            verbose=True,
            allow_delegation=False,
            max_iter=5,
            memory=True,
            step_callback=lambda x: print(x, "Title Writer Agent")
        )
class EmailTasks():
    
    def categorize_email(self, email_content, categorizer_agent):
        
        return Task(
            description=f"""
                Conduct a comprehensive analysis of the email provided and categorize into \
            one of the following categories:
            Job connection request: used when there is job request \
            Job Alerts: used when there is job alert \
            Job application: used when there is job application \
            Job endorsements: used when they are looking for professional skills \
            Job recommendation: used when there is job recommendation \
            Spam detection: Used when identifying spam emails via keywords, sender, content, behavior \
            Other: used when there is no job request, alert or application \
            Personal connection request: used when there is personal request \
            EMAIL CONTENT:\n\n {email_content} \n\n
            Output a single cetgory only""",

            expected_output="""A single categtory for the type of email from the types (Job connection request, Job Alerts, Job Application, Job endorsements, Job recommendation, Spam detection, Other, Personal connection request) \
            eg:
            Job connection request \
            """,
            agent=categorizer_agent
        )
    
    def research_info_for_email(self, email_content, categorize_email, researcher_agent):
        return Task(
            description=f"""Conduct a comprehensive analysis of the email provided and the category \
            provided and search the web to find info needed to respond to the email

            EMAIL CONTENT:\n\n {email_content} \n\n
            Only provide the info needed DONT try to write the email""",
            expected_output="""A set of bullet points of useful info for the email writer \
            or clear instructions that no useful material was found.""",
            context = [categorize_email],
            agent=researcher_agent
            )
    
    
    def draft_email(self, email_content, categorize_email, research_info_for_email, email_writer_agent):
        return Task(
            description=f"""Conduct a comprehensive analysis of the email provided, the category provided\
            and the info provided from the research specialist to write an email. \

            Write a simple, polite and too the point email which will respond to the provided email. \
            If useful use the info provided from the research specialist in the email. \

            If no useful info was provided from the research specialist the answer politely but don't make up info. \

            EMAIL CONTENT:\n\n {email_content} \n\n
            Output a single cetgory only""",
            expected_output="""A well crafted email for the customer that addresses their issues and concerns""",
            context = [categorize_email, research_info_for_email],
            agent=email_writer_agent,
            )
    
    def title_for_email(self, research_info_for_email, draft_email, title_writer_agent):
        return Task(
            description=f"""
                Write a title for the draft email provided. \
                The title should be short and to the point. \
                The title should be a summary of the email. \
                The title should be a single sentence. \
                if email content is not sufficient use research data\
                title should be less than 10-12 words
                """,
                expected_output="""A short title based on drafted email under 10 words""",
                context = [draft_email, research_info_for_email],
                agent=title_writer_agent,
        )
    

class UserAgent():
    def name_creater_agent(self):
        return Agent(
            role='name creator',
            goal="""
                Create a name for the user that is unique and easy to remember \
                it should be atleast of 3 words and atmost of 6 words  \
                it should be a mix of pokemon names, country names, numbers in words, cartoon names,
                planets names, animals within given range of words \
                make use of various unique words

                    
                """,
            backstory="""
                You are specialized and creative in giving names, with a good knowledge in tv shows, anime, science, maths etc
                """,
            llm=chatgroq,
            verbose=False,
            allow_delegation=False,
            max_iter=5,
            memory=True,
            step_callback=lambda x: print(x, "Name Creator Agent")

        )   

class UserTasks():
    def name_creator_task(self, creator_agent):
        return Task(
            description=f"""
            
                    think about various words that are been mostly introduced in anime , cartoon or it can be number word
                    gumble all those word and frame a mix sentence with minimum range of 3 words and maximum of 6 words
                    do make sure that next time same sentence should not be repeated
                    OUTPUT that mix name
                    """,
                    
            expected_output="""A single mix name unique and easy to remember name for the user
                e.g :
                mars shinchan fourty six lion
               """,
            
            agent=creator_agent
        )
    
def usersing():
    agents= UserAgent()
    tasks= UserTasks()

    creator_agent= agents.name_creater_agent()
    creator_task= tasks.name_creator_task(creator_agent)

    #define crew ai
    crew=Crew(
        agents=[creator_agent],
        tasks=[creator_task],
        verbose=2,
        process=Process.sequential,
        full_output=True,
        share_crew=False,
        step_callback=lambda x: print(x,"MasterCrew Agent")
    )

    result= crew.kickoff()
    return result['final_output']

def main(content:str):
    # with open('demo_email.txt', 'r', encoding='latin1')as f:
    #     email_content = f.read()
    #     content= email_content
    
    agents= EmailAgents()
    tasks= EmailTasks()

    #agents
    categorizer_agent= agents.make_categorizer_agent()
    researcher_agent= agents.make_researcher_agent()
    email_writer_agent= agents.make_email_writer_agent()
    title_writer_agent= agents.title_writer_agent()

    #tasks
    categorize_email= tasks.categorize_email(content, categorizer_agent)
    research_info_for_email= tasks.research_info_for_email(content, categorize_email, researcher_agent)
    draft_email= tasks.draft_email(content, categorize_email, research_info_for_email, email_writer_agent)
    title= tasks.title_for_email(research_info_for_email, draft_email, title_writer_agent)

    #define crew ai
    crew=Crew(
        agents=[categorizer_agent, researcher_agent, email_writer_agent, title_writer_agent],
        tasks=[categorize_email, research_info_for_email, draft_email, title],
        verbose=2,
        process=Process.sequential,
        full_output=True,
        share_crew=False,
        step_callback=lambda x: print_agent_chat(x,"MasterCrew Agent")
    )

    #defining data to be passed
    results=crew.kickoff()
    category=categorize_email.output.raw_output
    r_dt=research_info_for_email.output.raw_output
    emaill=draft_email.output.raw_output
    real_title= title.output.raw_output

    #data been shared
    data= {
        'email':emaill,
        'email_category': category,
        'email_research_data': r_dt,
        'title': real_title
    }

    return data


if __name__ == '__main__':
    usersing()









    


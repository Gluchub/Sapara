from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from main import *
from database_tester_firebaase import create_doc, create_user, retrieve_data,  chathistory_by_id, remove_data


app= FastAPI()

#mount css
app.mount('/static', StaticFiles(directory='static'), name='static')

#state templates
templates= Jinja2Templates(directory='templates')



def structure_text(text: str, command: str)-> str:
    # Replace the first comma
    if command=='email':
        first_comma_index = text.find(',')
        text = text[:first_comma_index] + ',</p><p class="mt-2 text-gray-400">' + text[first_comma_index+1:]

        # Replace the last comma
        last_comma_index = text.rfind(',')
        text = text[:last_comma_index] + ',</p><p class="block mt-1 text-lg leading-tight font-medium text-white">' + text[last_comma_index+1:]

        text= text.replace(':', ':<br>')
        text= text.replace('Dear', '<br>Dear')
        text_final= text.replace('.', '.<br>')

    elif command=='data':
        text_final= text.split('*')
        structured_str_sec=""
        for s in text_final:
            html_var=f"""<p class="mt-2 text-sm text-gray-600">{s}</p>"""
            structured_str_sec+=html_var
        # text_final= text.replace('.', '.<br>')
        text_final= structured_str_sec
    return text_final

@app.delete('/delete_chat/{chat_id}')
async def delete_chat(chat_id:str):
    # delete chat from database
    try:
        remove_data(chat_id)
        raise {"message": "Object deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting object: {e}")

@app.post('/get_titles', response_class=HTMLResponse)
async def sort_titles_by_name(request:Request, title:str = Form(...)):
    userName= title
    sortedtitles=[]
    all_data=retrieve_data()
    for chatid, chat_data in all_data.items():
        if chat_data['User']== userName:
            sortedtitles.append({'id':chatid, 'value':chat_data['Title']})
    
    return templates.TemplateResponse('form.html', {'request':request, 'sortedtitles':sortedtitles[-1]})


@app.get('/', response_class=HTMLResponse)
async def read_form(request: Request):
    titles=[]
    chathistory=retrieve_data()
    for chat_id, chat_data in  chathistory.items():
        titles.append({'id':chat_id ,'value':chat_data.get('Title')})
    titles.reverse()
    return templates.TemplateResponse('form.html', {'request': request, 'Titles':titles})

@app.get('/chathistory-details/{chat_id}', response_class=HTMLResponse)
async def get_chathistory_detail(request:Request,chat_id:str):
    titles=[]
    chathistory=retrieve_data()

    for chatid, chat_data in  chathistory.items():
        titles.append({'id':chatid ,'value':chat_data.get('Title')})
        

    titles.reverse()
    chathistory=chathistory_by_id(chat_id)
    values= chathistory.val()
    ai_response_category= values['Category']
    ai_email=values['GeneratedEmail']
    ai_response_email= structure_text(values['GeneratedEmail'], command='email')
    ai_response_researchdata= structure_text(values['ResearchData'], command='data')
    ai_submitted_text= structure_text(values['GivenEmail'], command='email')
    ai_user= values['User']



    return templates.TemplateResponse('form.html', {
        'request': request, 
        'values':values, 
        'Titles':titles, 
        'ai_user':ai_user,
        "ai_submitted_text":ai_submitted_text,
        'ai_response_category':ai_response_category ,
        'ai_response_email':ai_response_email,
        'ai_response_researchdata':ai_response_researchdata,
        'ai_email':ai_email
        })


@app.post("/process-text/", response_class=JSONResponse)
async def process_text(request: Request, text: str = Form(...)):
    titles=[]
    chathistory=retrieve_data()
    chat_id=None
    for chatid, chat_data in  chathistory.items():
        titles.append({'id':chatid ,'value':chat_data.get('Title')})
    ai_response = main(text)  # Call your AI agent's response function

    try:
        chatdata={
            'Title':ai_response['title'],
            'User':create_user(),
            'GeneratedEmail':ai_response['email'],
            'GivenEmail':text,
            'Category':ai_response['email_category'],
            'ResearchData':ai_response['email_research_data']
        }
        
        chat_id=create_doc(chatdata)

    except Exception as e:
        details_info='connection is slow we cant store your chat history'

    
    return JSONResponse(status_code=200, content={"chat_id": chat_id})




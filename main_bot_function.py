
import logging
import telegram
from telegram import InlineKeyboardMarkup,InlineKeyboardButton,Update,InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CallbackQueryHandler, ConversationHandler,ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, InlineQueryHandler
import pathlib
import os
import shutil
import requests
import backend_api


#log
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

#start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to F.A.T GPT bot, Please use /engine to select an engine, then /chat to start a conversation, or /idea to start a research, or /upload to upload a file for summarisation."
    )



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    #reply with text
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=text
        )


# to check if bot running
async def chat_with_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="You are now talking with F.A.T GPT-3 bot, enter text to start chat, or /refresh_gpt to clear the convo!"
        )
    return chat
    # text=update.message.text
    # #reply with text
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id, 
    #     text=context.user_data["engine"]
    #     )

    #reply with file
    # await context.bot.send_document(
    #     chat_id=update.effective_chat.id,``
    #     document="1.html"
    # )


    #reply with photo
    # with open("./image1.webp", 'rb') as f:
    #     file=f.read()

    # await context.bot.send_photo(chat_id=update.effective_chat.id,
    #     photo="image1.webp")

#reply inline query
# async def inline_caps(update: Update, `context: ContextTypes.DEFAULT_TYPE):
#     query = update.inline_query.query
#     print(query)
#     if not query:
#         return
#     results = []
#     results.append(
#         InlineQueryResultArticle(
#             id=query,
#             title='Caps',
#             input_message_content=InputTextMessageContent(query)
#         )
#     )
#     print(results)
#     await context.bot.answer_inline_query(update.inline_query.id, results)
    # inline_caps_handler = InlineQueryHandler(inline_caps)
    # application.add_handler(inline_caps_handler)


async def refresh_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("context")
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="You are now talking with F.A.T GPT-3 bot, enter text to start chat, or /refresh_gpt to clear the convo!"
        )
    return ConversationHandler.END

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "context" not in context.user_data:
        reply,chat_context=backend_api.context(update.message.text,"")
    else:
        reply,chat_context=backend_api.context(update.message.text,context.user_data["context"])

    context.user_data["context"]=chat_context
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=reply+"\n\n\nenter text to continue chat, or /refresh_gpt to clear the convo!"
        )

async def engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Semantic Scholar", callback_data="Semantic Scholar"),
            InlineKeyboardButton("Scopus", callback_data="Scopus"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose an engine:", 
                                    reply_markup=reply_markup)

async def engine_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    selection = update.callback_query.data
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=selection
    )
    context.user_data["engine"]=selection
    await update.callback_query.answer()


#receive file
async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file=await context.bot.get_file(update.message.document.file_id)


    folder_name=update.message.from_user.username

    
    
    keyboard = [
        [
            InlineKeyboardButton("Finish", callback_data="Finish"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Files received, once finished enter /finish,  to cancel enter /cancel:", reply_markup=reply_markup)
 
    await file.download_to_drive(folder_name+"/"+update.message.document.file_name)
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id, 
    #     text="received, when finish enter /finish, cancel enter /cancel")

#init upload
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    folder_name=update.message.from_user.username

    if(os.path.exists(folder_name)):
        shutil.rmtree(folder_name)
    os.mkdir(folder_name)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please enter the files you wish to have summarized. Enter /finish once complete, and /cancel if you wish to do something else"
    )
    return downloader
#end conversation




async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="F.A.T GPT bot is processing your files, please wait..."
    )
    directory=os.getcwd()+"/"+update.callback_query.from_user.username
    
    for filename in os.listdir(directory):
        summary,keywords_dict=backend_api.summarisation(os.path.join(directory, filename))
        keywords_str=""

        for i in keywords_dict["keywords"]:
            keywords_str+=i+", "

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="<b>"+filename+"</b>\n\n"+summary+"\n\n"+"<b>Related Keywords: </b>\n"+keywords_str[:-2],
            parse_mode="HTML"
        )

    return ConversationHandler.END

# remove the folder to cancel upload
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    folder_name=update.callback_query.from_user.username
    
    if(os.path.exists(folder_name)):
        shutil.rmtree(folder_name)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Upload Cancelled!"
    )
    return ConversationHandler.END



async def file_upload_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()
    
    if(query=="Finish"):
       await finish(update,context)
    elif(query=="Cancel"):
       await cancel(update,context)











# send file without /upload
async def send_file_without_upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter /upload to start an upload"
    )



async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["next_offset"]=0
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="The next message will be used to query for articles!"
    )
    return query



async def query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("here")

    if "query" not in context.user_data:
        context.user_data["query"]=update.message.text
        query=update.message.text
    else:
        query=context.user_data["query"]

    try:
        username=update.message.from_user.username
    except:
        username=update.callback_query.from_user.username
    print(query,2222222222)


    if(os.path.exists(username)):
        shutil.rmtree(username)
    os.mkdir(username)


    
    function={"Semantic Scholar":"SemanticScholar","Scopus":"scopus"}
    if "engine" not in context.user_data:
        context.user_data["engine"]="Semantic Scholar"
        result=eval("backend_api.SemanticScholar(query)")

    else:
        engine=function[context.user_data['engine']]
        result=eval("backend_api."+engine+"(query)")
    
    backend_api.CheckOpenAccess(result,username)


    file_list=[]
    directory=os.getcwd()+"/"+username

    for filename in os.listdir(directory):
        file_list.append(filename)
        


    output=""
    
    for article in result:
        if article[0]+".pdf" in file_list:
            print(article[0]+".pdf 66666")
            summary,keywords_dict=backend_api.summarisation(os.path.join(directory, article[0]+".pdf"))
            if summary=="":
                output+="<b>"+article[0]+"</b>\n\nFILE NOT FOUND!!!\n\n\n"
            else:

                output+="<b>"+article[0]+"</b>\n\n"+summary+"\n\nkeywords:\n"
                print(keywords_dict["keywords"])
                for keyword in keywords_dict["keywords"]:
                    output+=keyword+", "
                # for i in keywords_dict["keywords"]:
                #     keywords_str+=i+", "
                output=output[:-2]+"\n\n\n"
        else:
            output+="<b>"+article[0]+"</b>\n\nFILE NOT FOUND!!!\n\n\n"


    





    keyboard=[[]]
    concepts=backend_api.OpenAlexRelated(query)
    for each in concepts:
        keyboard[0].append(InlineKeyboardButton(each, callback_data=each))
            
 
    reply_markup = InlineKeyboardMarkup(keyboard)
    del context.user_data["query"]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Results retrived from "+context.user_data["engine"]+"\n\n\n\n"+output+"\n\n"+"continue type to query, or /query_finish to end",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def keyword_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = update.callback_query.data
    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Searching <b>"+keyword + "</b> Please wait...",
            parse_mode="HTML"
            )
    await update.callback_query.answer()
    context.user_data["query"]=keyword
    await query(update,context)


async def query_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Here are you files!"
    )
    return ConversationHandler.END



async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please enter /query_finish before using another command!"
    )


#wrap up
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Sorry, I didn't understand that command!")



if __name__ == '__main__':
    #bot token
    application = ApplicationBuilder().token('<YOUR TELEGRAM BOT TOKEN HERE>').build()
    
    #load bot handler 






    chat_handler=ConversationHandler(
        entry_points=[CommandHandler("chat",chat_with_gpt)],
        states={chat:[MessageHandler(filters.TEXT & (~filters.COMMAND), chat)]},
        fallbacks=[CommandHandler("refresh_gpt",refresh_gpt)]
    )
    application.add_handler(chat_handler)


# next:[CommandHandler("next", next)]
    query_handler=ConversationHandler(
        entry_points=[CommandHandler('idea', idea)],
        states={query:[MessageHandler(filters.TEXT & (~filters.COMMAND), query),
                       CallbackQueryHandler(keyword_button),
                       CommandHandler('query_finish', query_finish),
                       MessageHandler(filters.TEXT & filters.COMMAND,reject_command)],
                #next:[CommandHandler("next", next)],
              },
        fallbacks=[CommandHandler('query_finish', query_finish)])
    application.add_handler(query_handler)
 
 
    # use /upload to start an upload, then upload file as you like, 
    # choose /cancel to remove folders,
    # choose /finish to process the files
    file_reciever_handler=ConversationHandler(
        entry_points=[CommandHandler('upload', upload)],
        states={downloader:[MessageHandler(filters.Document.ALL, downloader)]},
        fallbacks=[CallbackQueryHandler(file_upload_button)])
    # file_reciever_handler=ConversationHandler(
    #     entry_points=[CommandHandler('upload', upload)],
    #     states={downloader:[MessageHandler(filters.Document.ALL, downloader)]},
    #     fallbacks=[CommandHandler('finish', finish),CommandHandler('cancel', cancel)])
    application.add_handler(file_reciever_handler)

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # must come after the file_reciever_handler!!!
    send_file_without_upload_cmd_handler=MessageHandler(filters.Document.ALL, send_file_without_upload_cmd)
    application.add_handler(send_file_without_upload_cmd_handler)

    engine_selection_handler=CallbackQueryHandler(engine_selection)
    application.add_handler(engine_selection_handler)
    engine_handler = CommandHandler('engine', engine)
    application.add_handler(engine_handler)

    # must come after everything
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    #launch
    print("running")
    application.run_polling()

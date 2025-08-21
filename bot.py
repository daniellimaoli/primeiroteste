import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler

TOKEN = "8449495417:AAGEK_y3E5P7byFe53A75_xZVj3Kswl8MUE"
CHAT_ID = "222005098"

# Estados para ConversationHandler
ADD_PRODUTO, ADD_QUANTIDADE = range(2)

# Ler produtos
df = pd.read_csv("produtos.csv", dtype={"observacoes": str})

def build_keyboard():
    keyboard = []
    for i, row in df.iterrows():
        marcado = row['observacoes']
        label = f"{row['produto']} (Qtd: {row['quantidade']})"
        if pd.notna(marcado) and marcado != "":
            label += " ✅"
        keyboard.append([InlineKeyboardButton(label, callback_data=str(i))])
    # Adiciona botão para novo produto
    keyboard.append([InlineKeyboardButton("➕ Adicionar produto", callback_data="add_produto")])
    return InlineKeyboardMarkup(keyboard)

async def enviar_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = build_keyboard()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🛒 Lista de Compras:\nClique para marcar produtos ou adicionar novo.",
        reply_markup=reply_markup
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Olá! Lista de compras interativa.")
    await enviar_lista(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_produto":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("Digite o nome do novo produto:", reply_markup=ReplyKeyboardRemove())
        return ADD_PRODUTO

    index = int(data)
    produto = df.loc[index, 'produto']

    # Alternar “marcado/desmarcado”
    marcado = df.loc[index, 'observacoes']
    if pd.isna(marcado) or marcado == "":
        df.loc[index, 'observacoes'] = "Marcado"
    else:
        df.loc[index, 'observacoes'] = ""

    # Salvar mudanças
    df.to_csv("produtos.csv", index=False)

    # Editar a mensagem original ao invés de enviar uma nova
    reply_markup = build_keyboard()
    await query.edit_message_reply_markup(reply_markup=reply_markup)
    return ConversationHandler.END

async def add_produto_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['novo_produto'] = update.message.text.strip()
    await update.message.reply_text("Digite a quantidade:")
    return ADD_QUANTIDADE

async def add_produto_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    quantidade = update.message.text.strip()
    produto = context.user_data['novo_produto']

    # Adiciona novo produto ao DataFrame
    nova_linha = {
        'produto': produto,
        'quantidade': quantidade,
        'observacoes': ""
    }
    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
    df.to_csv("produtos.csv", index=False)

    await update.message.reply_text(f"Produto '{produto}' adicionado com quantidade {quantidade}!", reply_markup=ReplyKeyboardRemove())
    await enviar_lista(update, context)
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Criar aplicação do bot
app = ApplicationBuilder().token(TOKEN).build()

# ConversationHandler para adicionar produto
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button)],
    states={
        ADD_PRODUTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_produto_nome)],
        ADD_QUANTIDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_produto_quantidade)],
    },
    fallbacks=[CommandHandler("cancelar", cancelar)],
    per_chat=True
)

# Adicionar handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lista", enviar_lista))
app.add_handler(conv_handler)

# Rodar bot
app.run_polling()

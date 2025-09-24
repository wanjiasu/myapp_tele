import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 加载环境变量
load_dotenv()

# 启用日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/start命令，显示欢迎消息和注册按钮"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # 生成注册链接
    site_url = os.getenv('site_url', 'http://localhost:3000')
    register_url = f"{site_url}/signup?tg_user_id={user.id}&tg_chat_id={chat_id}"
    
    # 欢迎消息
    message = (
        f"🎉 欢迎，{user.first_name}！\n\n"
        f"欢迎使用我们的服务！请选择以下操作："
    )
    
    # 创建内联键盘按钮 - 使用 URL 按钮直接跳转
    keyboard = [
        [
            InlineKeyboardButton("🚀 立即注册", url=register_url),
            InlineKeyboardButton("✅ 我已注册", callback_data="already_registered")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 发送消息和按钮
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    # 记录日志
    logger.info(f"用户 {user.id} 启动bot，注册链接: {register_url}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理按钮点击回调"""
    query = update.callback_query
    user = query.from_user
    
    # 确认回调查询
    await query.answer()
    
    if query.data == "already_registered":
        # 用户点击"我已注册"按钮
        message = (
            f"✅ 欢迎回来！\n\n"
            f"您已经是我们的注册用户了。\n"
            f"如需帮助，请联系客服。"
        )
        
        # 创建返回按钮
        keyboard = [
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        logger.info(f"用户 {user.id} 点击我已注册按钮")
        
    elif query.data == "back_to_main":
        # 返回主菜单
        chat_id = query.message.chat.id
        
        # 生成注册链接
        site_url = os.getenv('site_url', 'http://localhost:3000')
        register_url = f"{site_url}/signup?tg_user_id={user.id}&tg_chat_id={chat_id}"
        
        message = (
            f"🎉 欢迎，{user.first_name}！\n\n"
            f"欢迎使用我们的服务！请选择以下操作："
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🚀 立即注册", url=register_url),
                InlineKeyboardButton("✅ 我已注册", callback_data="already_registered")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        logger.info(f"用户 {user.id} 返回主菜单")


def main() -> None:
    """启动bot"""
    # 从环境变量获取Bot Token
    BOT_TOKEN = os.getenv('bot_token')
    
    if not BOT_TOKEN:
        print("错误：未找到bot_token环境变量")
        return
    
    # 创建Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    
    # 添加回调查询处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 运行bot
    print("Bot启动中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
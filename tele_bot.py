import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, jsonify
import asyncio
import threading

# 加载环境变量
load_dotenv()

# 启用日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用用于接收绑定成功通知
app = Flask(__name__)

# 全局变量存储 bot 实例
bot_instance = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理/start命令，显示欢迎消息和绑定按钮"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # 生成登录链接（带 Telegram 参数）
    site_url = os.getenv('site_url', 'http://localhost:3000')
    login_url = f"{site_url}/login?tg_user_id={user.id}&tg_chat_id={chat_id}"
    
    # 欢迎消息
    message = (
        f"🎉 欢迎，{user.first_name}！\n\n"
        f"点击下方按钮绑定您的账户，享受完整服务体验！"
    )
    
    # 创建内联键盘按钮 - 只有一个绑定按钮
    keyboard = [
        [InlineKeyboardButton("🔗 立即绑定", url=login_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 发送消息和按钮
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    # 记录日志
    logger.info(f"用户 {user.id} 启动bot，绑定链接: {login_url}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理按钮点击回调（现在主要用于处理返回主菜单等操作）"""
    query = update.callback_query
    user = query.from_user
    
    # 确认回调查询
    await query.answer()
    
    if query.data == "back_to_main":
        # 返回主菜单
        chat_id = query.message.chat.id
        
        # 生成登录链接（带 Telegram 参数）
        site_url = os.getenv('site_url', 'http://localhost:3000')
        login_url = f"{site_url}/login?tg_user_id={user.id}&tg_chat_id={chat_id}"
        
        message = (
            f"🎉 欢迎，{user.first_name}！\n\n"
            f"点击下方按钮绑定您的账户，享受完整服务体验！"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔗 立即绑定", url=login_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        logger.info(f"用户 {user.id} 返回主菜单")


async def send_binding_success_message(chat_id: int, user_name: str) -> None:
    """发送绑定成功的祝贺消息"""
    try:
        message = (
            f"🎉 恭喜 {user_name}！\n\n"
            f"✅ 账户绑定成功！\n"
            f"🚀 现在您可以享受完整的服务体验了！\n\n"
            f"感谢您的使用！"
        )
        
        # 创建返回主菜单的按钮
        keyboard = [
            [InlineKeyboardButton("🏠 返回主菜单", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot_instance.send_message(
            chat_id=chat_id, 
            text=message, 
            reply_markup=reply_markup
        )
        logger.info(f"已向用户 {chat_id} 发送绑定成功消息")
    except Exception as e:
        logger.error(f"发送绑定成功消息失败: {e}")


@app.route('/binding-success', methods=['POST'])
def handle_binding_success():
    """处理绑定成功的 webhook"""
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        user_name = data.get('user_name', '用户')
        
        if not chat_id:
            return jsonify({'error': 'chat_id is required'}), 400
        
        # 在新的事件循环中发送消息
        def send_message():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_binding_success_message(chat_id, user_name))
            loop.close()
        
        # 在新线程中运行异步函数
        threading.Thread(target=send_message).start()
        
        return jsonify({'status': 'success', 'message': 'Binding success message sent'})
    
    except Exception as e:
        logger.error(f"处理绑定成功通知失败: {e}")
        return jsonify({'error': str(e)}), 500


def run_flask_app():
    """运行 Flask 应用"""
    app.run(host='0.0.0.0', port=5001, debug=False)


def main() -> None:
    """启动bot"""
    global bot_instance
    
    # 从环境变量获取Bot Token
    BOT_TOKEN = os.getenv('bot_token')
    
    if not BOT_TOKEN:
        print("错误：未找到bot_token环境变量")
        return
    
    # 创建Bot实例
    bot_instance = Bot(token=BOT_TOKEN)
    
    # 创建Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    
    # 添加回调查询处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 在新线程中启动 Flask 应用
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # 运行bot
    print("Bot启动中...")
    print("Flask webhook 服务运行在 http://localhost:5001")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()